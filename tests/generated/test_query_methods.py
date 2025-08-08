# === Tests for `is_cacheable` ===
import pytest
from tinydb import Query

def test_is_cacheable_true():
    q = Query()
    q._hash = 12345
    assert q.is_cacheable() is True

def test_is_cacheable_false():
    q = Query()
    q._hash = None
    assert q.is_cacheable() is False

# === Tests for `exists` ===
import pytest
from tinydb import Query
from tinydb.storages import MemoryStorage


def test_exists_basic():
    q = Query()
    assert q.f1.exists() == {'f1': {'$exists': True}}


def test_exists_nested():
    q = Query()
    assert q.f1.f2.exists() == {'f1': {'f2': {'$exists': True}}}


def test_exists_with_other_tests():
    q = Query()
    test_query = (q.f1.exists() & q.f2 == 2) | q.f3.test(lambda x: x > 3)
    assert test_query == {
        '$or': [
            {'$and': [{'f1': {'$exists': True}}, {'f2': 2}]},
            {'f3': {'$test': lambda x: x > 3}},
        ]
    }



def test_exists_integration_true(tmpdir):
    from tinydb import TinyDB

    with TinyDB(storage=MemoryStorage) as db:
        db.insert({'f1': 1})

        assert db.search(Query().f1.exists()) == [{'f1': 1}]


def test_exists_integration_false(tmpdir):
    from tinydb import TinyDB
    with TinyDB(storage=MemoryStorage) as db:

        assert db.search(Query().f1.exists()) == []

        db.insert({'f2': 1})  # Insert a document without 'f1'

        assert db.search(Query().f1.exists()) == []

# === Tests for `matches` ===
import re
from tinydb import Query
import pytest

def test_matches_string_match():
    User = Query()
    assert User.name.matches(r'^\\w+$').test({'name': '_'}) is True

def test_matches_string_no_match():
    User = Query()
    assert User.name.matches(r'^\\w+$').test({'name': '-'}) is False

def test_matches_not_string():
    User = Query()
    assert User.name.matches(r'^\\w+$').test({'name': 123}) is False

def test_matches_none():
    User = Query()
    assert User.name.matches(r'^\\w+$').test({'name': None}) is False

def test_matches_flags():
    User = Query()
    assert User.name.matches(r'^[a-z]+$', flags=re.IGNORECASE).test({'name': 'Abc'}) is True

def test_matches_missing_field():
    User = Query()
    assert User.name.matches(r'^\\w+$').test({}) is False

def test_matches_nested_match():
    User = Query()
    assert User.address.street.matches(r'^\\d+$').test({'address': {'street': '123'}}) is True

def test_matches_nested_no_match():
    User = Query()
    assert User.address.street.matches(r'^\\d+$').test({'address': {'street': 'abc'}}) is False

def test_matches_nested_missing_field():
    User = Query()
    assert User.address.street.matches(r'^\\d+$').test({'address': {}}) is False
    assert User.address.street.matches(r'^\\d+$').test({}) is False


def test_matches_generate_test_arguments():
    User = Query()
    query = User.name.matches(r'^\\w+$')

    test_func, test_args = query.test, query.test_args

    assert test_func({'name': '_'}) is True
    assert test_args == ('matches', ['name'], r'^\\w+$')

# === Tests for `search` ===
import re
from tinydb import Query
import pytest


def test_search_match():
    User = Query()
    assert User.name.search('^test$').test(value='test')


def test_search_no_match():
    User = Query()
    assert not User.name.search('^test$').test(value='Test')


def test_search_substring_match():
    User = Query()
    assert User.name.search('es').test(value='test')

def test_search_flags():
    User = Query()
    assert User.name.search('^test$', flags=re.IGNORECASE).test(value='Test')


def test_search_non_string_value():
    User = Query()
    assert not User.name.search('^test$').test(value=123)

def test_search_empty_string():
    User = Query()
    assert User.name.search('').test(value='test')

def test_search_none_value():
    User = Query()
    assert not User.name.search('^test$').test(value=None)


def test_search_generate_test_output():
    User = Query()
    test = User.name.search('^test$')
    assert test._test(('search', ['name'], '^test$')) == test.test

def test_search_unicode():
    User = Query()
    assert User.name.search('^üñîçødé$').test(value='üñîçødé')

def test_search_complex_regex():
    User = Query()
    regex = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    assert User.email.search(regex).test(value="test@example.com")
    assert not User.email.search(regex).test(value="invalid-email")



# === Tests for `test` ==
import pytest
from tinydb import TinyDB, Query
from tinydb.storages import MemoryStorage
from typing import Callable, Mapping

def test_query_test_simple():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'f1': 42})
    db.insert({'f1': 24})

    def test_func(val):
        return val == 42

    User = Query()
    results = db.search(User.f1.test(test_func))
    assert len(results) == 1
    assert results[0]['f1'] == 42


def test_query_test_with_args():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'f1': "hello world"})
    db.insert({'f1': "hello"})

    def test_func(val, substr):
        return substr in val

    User = Query()
    results = db.search(User.f1.test(test_func, "world"))
    assert len(results) == 1
    assert results[0]['f1'] == "hello world"

def test_query_test_no_match():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'f1': 10})
    db.insert({'f1': 20})

    def test_func(val):
        return val == 42

    User = Query()
    results = db.search(User.f1.test(test_func))
    assert len(results) == 0


def test_query_test_nested_field():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'f1': {'f2': 42}})
    db.insert({'f1': {'f2': 24}})


    def test_func(val):
        return val == 42

    User = Query()
    results = db.search(User.f1.f2.test(test_func))
    assert len(results) == 1
    assert results[0]['f1']['f2'] == 42

def test_query_test_invalid_data():
    db = TinyDB(storage=MemoryStorage)
    db.insert({'f1': 10})

    def test_func(val: Mapping): # Expecting a mapping
        return val['nonexistent_key'] == 42  # Accessing key that doesn't exist

    User = Query()
    with pytest.raises(KeyError):  # Expect KeyError when accessing non-existent key
        db.search(User.f1.test(test_func))

# === Tests for `any` ===
import pytest
from tinydb.queries import Query, is_sequence
from tinydb.utils import freeze

def test_query_any_with_query():
    query = Query().f1.any(Query().f2 == 1)
    assert query({'f1': [{'f2': 1}, {'f2': 0}]})
    assert not query({'f1': [{'f2': 0}, {'f2': 0}]})
    assert not query({'f1': []})
    assert not query({})

def test_query_any_with_list():
    query = Query().f1.any([1, 2, 3])
    assert query({'f1': [1, 2]})
    assert query({'f1': [3, 4, 5]})
    assert not query({'f1': [4, 5, 6]})
    assert not query({'f1': []})
    assert not query({})

def test_query_any_with_empty_list():
    query = Query().f1.any([])
    assert not query({'f1': [1, 2]})
    assert not query({'f1': []})
    assert not query({})


def test_query_any_callable():
    query = Query().f1.any(lambda x: x == 2)
    assert query({'f1': [1, 2, 3]})
    assert not query({'f1': [1, 3]})

def test_query_any_non_sequence():
    query = Query().f1.any([1, 2, 3])
    assert not query({'f1': 1})
    assert not query({})

def test_query_any_nested_query():
    query = Query().f1.any(Query().f2.any([1, 2]))
    assert query({'f1': [{'f2': [1, 3]}, {'f2': [4]}]})
    assert not query({'f1': [{'f2': [3]}, {'f2': [4]}]})


def test_freeze_cond():
    cond = [1, 2, {'a': 3}]
    query = Query().f1.any(cond)
    frozen_cond = query.test[2][2]  # Access the frozen condition
    assert frozen_cond == freeze(cond)
    assert isinstance(frozen_cond, tuple)  # Check if frozen to tuple
    assert isinstance(frozen_cond[2], tuple) # Check for correct nested tuple


def test_is_sequence_string():
    query = Query().f1.any("test")
    assert not query({'f1': "test"}) # Should not match if the value is a string
    assert query({'f1': ['t','e']})  # Should work for list of strings
    assert query({'f1': list("test")})


# === Tests for `all` ===
import pytest
from tinydb.queries import Query, QueryInstance
from tinydb.utils import freeze
from typing import List, Any, Union
from collections.abc import Sequence


def is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence)


@pytest.mark.parametrize('value, cond, expected', [
    ([{'f2': 1}, {'f2': 1}], Query().f2 == 1, True),
    ([{'f2': 1}, {'f2': 2}], Query().f2 == 1, False),
    ([1, 2, 3, 4, 5], [1, 2, 3], True),
    ([1, 2, 4, 5], [1, 2, 3], False),
    (1, [1, 2, 3], False),  # Non-sequence value
    ([{'f2': 1}], 1, False),  # Non-callable and non-list cond
])
def test_all_query(value, cond, expected):
    q = Query()
    result = q.f1.all(cond)
    assert result({'f1': value}) == expected


@pytest.mark.parametrize('cond', [
    1,
    "string",
    {'a': 1},
])
def test_all_invalid_cond_type(cond):
    q = Query()
    with pytest.raises(TypeError):
        q.f1.all(cond)


def test_all_callable_cond():
    q = Query()
    result = q.f1.all(lambda x: x > 2)
    assert result({'f1': [3, 4, 5]}) == True
    assert result({'f1': [1, 2, 3]}) == False


def test_all_generate_test_structure():
    q = Query()
    cond = [1, 2, 3]
    result = q.f1.all(cond)

    assert isinstance(result, QueryInstance)
    assert result.test.__name__ == 'test'  # Check for inner function name
    assert result.lookups == ('all', ['f1'], freeze(cond))


# === Tests for `one_of` ===
import pytest
from tinydb import Query
from tinydb.utils import freeze


def test_one_of_list():
    query = Query().f1.one_of(['value 1', 'value 2'])
    assert query({'f1': 'value 1'})
    assert query({'f1': 'value 2'})
    assert not query({'f1': 'value 3'})
    assert not query({'f1': None})


def test_one_of_generator():
    items = (f'value {i}' for i in range(1, 3))
    query = Query().f1.one_of(items)
    assert query({'f1': 'value 1'})
    assert query({'f1': 'value 2'})
    assert not query({'f1': 'value 3'})
    assert not query({'f1': None})

def test_one_of_empty_list():
    query = Query().f1.one_of([])
    assert not query({'f1': 'value 1'})
    assert not query({'f1': None})

def test_one_of_nested_list():
    query = Query().f1.one_of([['nested1'], ['nested2']])
    assert query({'f1': ['nested1']})
    assert query({'f1': ['nested2']})
    assert not query({'f1': ['nested3']})
    assert not query({'f1': 'nested1'}) # type mismatch

def test_one_of_freeze():
    items = {'key': 'value'}
    query = Query().f1.one_of([items])
    assert query({'f1': freeze(items)})
    assert not query({'f1': items}) # not frozen


def test_one_of_callable_items():
    items = [lambda x: x > 5]
    with pytest.raises(TypeError, match="cannot compare using 'in' with a callable"):
        Query().f1.one_of(items)
# === Tests for `fragment` ===
import pytest
from tinydb import Query
from tinydb.utils import freeze


def test_fragment_match():
    User = Query()
    document = {'name': 'John', 'age': 30}
    query = User.fragment(document)
    assert query({'name': 'John', 'age': 30, 'city': 'New York'})


def test_fragment_partial_match():
    User = Query()
    document = {'name': 'John', 'age': 30}
    query = User.fragment(document)
    assert not query({'name': 'John'})


def test_fragment_mismatch():
    User = Query()
    document = {'name': 'John', 'age': 30}
    query = User.fragment(document)
    assert not query({'name': 'Jane', 'age': 30})


def test_fragment_different_type():
    User = Query()
    document = {'name': 'John', 'age': 30}
    query = User.fragment(document)
    assert not query([{'name': 'John'}, {'age': 30}])


def test_fragment_empty_document():
    User = Query()
    document = {}
    query = User.fragment(document)
    assert query({'name': 'John', 'age': 30})


def test_fragment_nested_document():
    User = Query()
    document = {'address': {'street': 'Main St', 'city': 'Anytown'}}
    query = User.fragment(document)
    assert query({'name': 'John', 'address': {'street': 'Main St', 'city': 'Anytown'}})


def test_fragment_nested_document_mismatch():
    User = Query()
    document = {'address': {'street': 'Main St', 'city': 'Anytown'}}
    query = User.fragment(document)
    assert not query({'address': {'street': 'Main St'}})



def test_fragment_with_list():
  User = Query()
  document = {'items': ['apple', 'banana']}
  query = User.fragment(document)
  assert query({'items': ['apple', 'banana'], 'price': 10})


def test_fragment_with_list_mismatch():
    User = Query()
    document = {'items': ['apple', 'banana']}
    query = User.fragment(document)
    assert not query({'items': ['apple']})

def test_fragment_generate_test_structure():
    User = Query()
    document = {'name': 'John', 'age': 30}
    query = User.fragment(document)
    test_func, test_name, _ = query.test

    assert test_name == ('fragment', freeze(document))
    assert test_func({'name': 'John', 'age': 30}) == True
    assert test_func({'name': 'Jane', 'age': 30}) == False


# === Tests for `noop` ===
import pytest
from tinydb.queries import Query, QueryInstance

def test_query_noop():
    User = Query()
    assert User.noop() == QueryInstance(lambda value: True, ())
    assert User.noop().test(None) is True
    assert User.noop().test(1) is True
    assert User.noop().test("value") is True
    assert User.noop().test({"key": "value"}) is True
    assert User.noop().test([1, 2, 3]) is True


# === Tests for `map` ===
import pytest
from tinydb import Query
from typing import Callable


def test_query_map_simple():
    q = Query()
    mapped_q = q.map(lambda x: x + 1)

    assert mapped_q._path == (lambda x: x + 1,)
    assert mapped_q._hash is None
    assert q._path == ()


def test_query_map_chained():
    q = Query()
    mapped_q = q.map(lambda x: x + 1).map(lambda x: x * 2)

    assert mapped_q._path == (lambda x: x + 1, lambda x: x * 2)
    assert mapped_q._hash is None


def test_query_map_with_existing_path():
    q = Query().name
    mapped_q = q.map(lambda x: x.upper())

    assert mapped_q._path == ('name', lambda x: x.upper())
    assert mapped_q._hash is None


def test_query_map_mutable_callable():
    state = {'value': 1}

    def mutable_fn(x):
        state['value'] += 1
        return x + state['value']

    q = Query()
    mapped_q1 = q.map(mutable_fn)
    mapped_q2 = q.map(mutable_fn)


    assert mapped_q1._path == (mutable_fn,)
    assert mapped_q2._path == (mutable_fn,)
    assert mapped_q1._hash is None
    assert mapped_q2._hash is None

    assert q._path == ()
    assert q._hash is not None
