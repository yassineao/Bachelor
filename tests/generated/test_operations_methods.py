# === Tests for `delete` ===

import pytest
from tinydb.operations import delete

def test_delete_existing_field():
    doc = {'a': 1, 'b': 2}
    transform = delete('a')
    transform(doc)
    assert doc == {'b': 2}


def test_delete_nonexisting_field():
    doc = {'a': 1, 'b': 2}
    transform = delete('c')
    with pytest.raises(KeyError):
        transform(doc)


def test_delete_nested_field():
    doc = {'a': {'b': 1, 'c': 2}}
    transform = delete('a.b')  # This won't work as delete operates on top-level keys
    with pytest.raises(KeyError):
        transform(doc)


def test_delete_from_empty_doc():
    doc = {}
    transform = delete('a')
    with pytest.raises(KeyError):
        transform(doc)


def test_delete_with_none_field():
    doc = {'a': 1}
    with pytest.raises(TypeError, match=r"string indices must be integers, not 'NoneType'"):  # Or similar error depending on Python version
        delete(None)(doc)



def test_delete_with_int_field():
    doc = {1: 1}
    transform = delete(1)
    transform(doc)
    assert doc == {}



def test_delete_with_non_string_field():
     doc = {1: 1}
     transform = delete(1)
     transform(doc)
     assert doc == {}

def test_delete_all_fields():
    doc = {'a': 1, 'b': 2, 'c': 3}

    transform_a = delete('a')
    transform_b = delete('b')
    transform_c = delete('c')

    transform_a(doc)
    transform_b(doc)
    transform_c(doc)

    assert doc == {}

def test_delete_from_list_within_dict_incorrectly(): # Demonstrating that delete doesn't handle lists
    doc = {'a': [1, 2, 3]}
    transform = delete('a.0')  # Trying to delete an element from a list
    with pytest.raises(KeyError):  # delete doesn't handle this, expect KeyError
        transform(doc)

def test_delete_with_empty_string_key():
    doc = {'': 1, 'a': 2}
    transform = delete('')
    transform(doc)
    assert doc == {'a': 2}



# === Tests for `add` ===
import pytest
from tinydb.operations import add

def test_add_positive():
    transform = add('value', 5)
    doc = {'value': 10}
    transform(doc)
    assert doc == {'value': 15}

def test_add_negative():
    transform = add('value', -5)
    doc = {'value': 10}
    transform(doc)
    assert doc == {'value': 5}

def test_add_float():
    transform = add('value', 3.14)
    doc = {'value': 1.0}
    transform(doc)
    assert doc == {'value': 4.14}

def test_add_to_zero():
    transform = add('value', 5)
    doc = {'value': 0}
    transform(doc)
    assert doc == {'value': 5}


def test_add_to_nonexistent_field():
    transform = add('value', 5)
    doc = {}
    with pytest.raises(KeyError):
        transform(doc)


def test_add_non_numeric():
    transform = add('value', 5)
    doc = {'value': 'abc'}
    with pytest.raises(TypeError):  # Expecting TypeError for string + int
        transform(doc)

def test_add_to_list():
    transform = add('value', [1,2])  # Adding a list to a potentially existing list.
    doc = {'value': [0]}
    transform(doc)
    assert doc == {'value': [0, 1, 2]}


def test_add_none():
    transform = add('value', None)
    doc = {'value': 10}
    with pytest.raises(TypeError):
        transform(doc)

def test_add_nested_field_positive():
    transform = add('nested.value', 5)
    doc = {'nested': {'value': 10}}
    transform(doc)
    assert doc == {'nested': {'value': 15}}


def test_add_nested_field_nonexistent():
    transform = add('nested.value', 5)
    doc = {}  # No 'nested' key.
    with pytest.raises(KeyError):
        transform(doc)



def test_add_nested_field_partial_nonexistent():
    transform = add('nested.value', 5)
    doc = {'nested': {}} # 'nested' exists but 'value' does not.
    with pytest.raises(KeyError):
        transform(doc)


# === Tests for `subtract` ===
import pytest
from tinydb.operations import subtract

def test_subtract_positive():
    doc = {'a': 5}
    transform = subtract('a', 2)
    transform(doc)
    assert doc == {'a': 3}


def test_subtract_negative():
    doc = {'a': 5}
    transform = subtract('a', -2)
    transform(doc)
    assert doc == {'a': 7}


def test_subtract_zero():
    doc = {'a': 5}
    transform = subtract('a', 0)
    transform(doc)
    assert doc == {'a': 5}


def test_subtract_float():
    doc = {'a': 5.5}
    transform = subtract('a', 2.5)
    transform(doc)
    assert doc == {'a': 3.0}


def test_subtract_from_zero():
    doc = {'a': 0}
    transform = subtract('a', 5)
    transform(doc)
    assert doc == {'a': -5}


def test_subtract_missing_field():
    doc = {}
    transform = subtract('a', 5)
    with pytest.raises(KeyError):
       transform(doc)


def test_subtract_non_numeric_field_int():
    doc = {'a': 'hello'}
    transform = subtract('a', 5)
    with pytest.raises(TypeError):  # Expect TypeError for string subtraction
        transform(doc)

def test_subtract_non_numeric_field_float():
    doc = {'a': 'hello'}
    transform = subtract('a', 5.5)
    with pytest.raises(TypeError): # Expect TypeError for string subtraction
        transform(doc)


def test_subtract_non_numeric_subtrahend():
    doc = {'a': 5}
    transform = subtract('a', 'hello')
    with pytest.raises(TypeError): # Expect TypeError for subtracting a string
        transform(doc)


def test_subtract_nested_field():
    doc = {'a': {'b': 5}}
    transform = subtract('a.b', 2)  # Note: TinyDB does *not* support nested fields directly with operations
    with pytest.raises(KeyError): # Expect KeyError because nested field access isn't directly supported.
       transform(doc)

def test_subtract_list_element():
    doc = {'a': [1, 2, 3]}
    transform = subtract('a[1]', 1)  # TinyDB doesn't support direct list element modification with operations.
    with pytest.raises(KeyError): # Expect KeyError because list element access isn't directly supported.
        transform(doc)


def test_subtract_from_none():
    doc = {'a': None}
    transform = subtract('a', 5)
    with pytest.raises(TypeError): # Expect TypeError since subtracting from None isn't allowed.
        transform(doc)

# === Tests for `set` ===
import pytest
from tinydb.operations import set


@pytest.mark.parametrize('field, val, doc, expected', [
    ('name', 'John', {'age': 30}, {'name': 'John', 'age': 30}),
    ('age', 40, {'name': 'John', 'age': 30}, {'name': 'John', 'age': 40}),
    ('city', 'New York', {}, {'city': 'New York'}),
    ('nested.field', 10, {'nested': {'field': 5}}, {'nested': {'field': 10}}),
    ('list_field', [1, 2, 3], {'list_field': []}, {'list_field': [1, 2, 3]}),
    ('None_val', None, {'a': 1}, {'None_val': None, 'a': 1}),
    ('int_field', 123, {'int_field': '123'}, {'int_field': 123}),
    ('bool_field', True, {'bool_field': False}, {'bool_field': True}),
    ('float_field', 3.14, {'float_field': 1.23}, {'float_field': 3.14}),

])
def test_set_operation(field, val, doc, expected):
    transform = set(field, val)
    new_doc = transform(doc.copy())  # Ensure original doc isn't modified
    assert new_doc == expected


def test_set_operation_with_empty_string_field():
    doc = {'name': 'John'}
    transform = set('', 'Doe')  # Field name is empty
    new_doc = transform(doc.copy())
    assert new_doc == {'': 'Doe', 'name': 'John'}

def test_set_operation_with_none_field():
    doc = {'name': 'John'}
    transform = set(None, 'Doe')  # Field name is None
    new_doc = transform(doc.copy())
    assert new_doc == {None: 'Doe', 'name': 'John'}




# === Tests for `increment` ===
import pytest
from tinydb.operations import increment

def test_increment_existing_field():
    doc = {'a': 1}
    transform = increment('a')
    transform(doc)
    assert doc == {'a': 2}

def test_increment_nonexisting_field():
    doc = {}
    transform = increment('a')
    with pytest.raises(KeyError):
        transform(doc)


def test_increment_none_field():
    doc = {'a': None}
    transform = increment('a')
    with pytest.raises(TypeError):  # Cannot increment None
        transform(doc)

def test_increment_string_field():
    doc = {'a': "hello"}
    transform = increment('a')
    with pytest.raises(TypeError): # Cannot increment string
        transform(doc)

def test_increment_list_field():
    doc = {'a': [1,2,3]}
    transform = increment('a')
    with pytest.raises(TypeError): # Cannot increment list
        transform(doc)

def test_increment_float_field():
    doc = {'a': 1.5}
    transform = increment('a')
    transform(doc)
    assert doc == {'a': 2.5}

def test_increment_int_field_large_number():
    doc = {'a': 100000000000000000000000000000000000000}
    transform = increment('a')
    transform(doc)
    assert doc == {'a': 100000000000000000000000000000000000001}

def test_increment_nested_field_existing():
    doc = {'a': {'b': 1}}
    transform = increment('a.b')  # This won't work with basic increment.
    with pytest.raises(KeyError):  # Illustrates that nested fields are not supported by default.
      transform(doc)

    # Demonstrating how this would fail without specific nesting support.
    # This does not cause a failure, but the doc remains unchanged.
    #  (In a more advanced implementation, you'd use update with nested field support here)


# === Tests for `decrement` ===
import pytest

from tinydb.operations import decrement

def test_decrement_existing_field():
    doc = {'a': 5}
    transform = decrement('a')
    transform(doc)
    assert doc == {'a': 4}


def test_decrement_nonexisting_field():
    doc = {'a': 5}
    transform = decrement('b')
    with pytest.raises(KeyError):
        transform(doc)


def test_decrement_non_int_field():
    doc = {'a': 'string'}
    transform = decrement('a')
    with pytest.raises(TypeError):
        transform(doc)


def test_decrement_float_field():
    doc = {'a': 5.5}
    transform = decrement('a')
    transform(doc)
    assert doc == {'a': 4.5}


def test_decrement_zero_value():
    doc = {'a': 0}
    transform = decrement('a')
    transform(doc)
    assert doc == {'a': -1}



def test_decrement_negative_value():
    doc = {'a': -5}
    transform = decrement('a')
    transform(doc)
    assert doc == {'a': -6}


def test_decrement_nested_field():
    doc = {'a': {'b': 5}}
    transform = decrement('a.b')  # Assuming dotted path is supported (not explicitly mentioned)

    with pytest.raises(KeyError):  # Should raise KeyError as nested decrement not directly supported
        transform(doc)



def test_decrement_empty_document():
    doc = {}
    transform = decrement('a')
    with pytest.raises(KeyError):
        transform(doc)

