# === Tests for `with_typehint` ===

from typing import TYPE_CHECKING, Type, TypeVar

import pytest

from tinydb.utils import with_typehint

T = TypeVar("T")


class TestWithTypehint:
    def test_type_checking(self):
        """Verify behavior during type checking."""

        class Bar:
            x: int

        class Foo(with_typehint(Bar)):
            pass

        if TYPE_CHECKING:
            assert issubclass(Foo, Bar)  # Expected behavior during type checking
        else:
            assert not issubclass(Foo, Bar) # Should not be a subclass at runtime

    def test_runtime(self):
        """Verify runtime behavior."""

        class Bar:
            pass

        class Foo(with_typehint(Bar)):
            pass

        assert issubclass(Foo, object)
        assert not issubclass(Foo, Bar)  # Should not inherit from Bar at runtime

    def test_attribute_access_type_checking(self):
        """Test attribute access during type checking."""
        if not TYPE_CHECKING:
            pytest.skip("This test only runs during type checking")

        class Bar:
            x: int

        class Foo(with_typehint(Bar)):
            def __init__(self):
                self.x = "wrong type"  # This should cause a type error during type checking

        foo = Foo()  # Type checker should complain about the assignment in __init__


    def test_attribute_access_runtime(self):
        """Test attribute access at runtime (no type errors expected)."""

        class Bar:
            x: int

        class Foo(with_typehint(Bar)):
            def __init__(self):
                self.x = "wrong type"

        foo = Foo()
        assert foo.x == "wrong type"  # No type error at runtime




# === Tests for `LRUCache` ===
from collections import OrderedDict
from typing import Generic, Iterator, List, Optional, TypeVar, Union

import pytest

from tinydb.utils import LRUCache

K = TypeVar("K")
V = TypeVar("V")
D = TypeVar("D")


def test_lru_cache_basic():
    cache = LRUCache(2)
    cache["a"] = 1
    cache["b"] = 2
    assert cache["a"] == 1
    cache["c"] = 3
    assert "b" not in cache
    assert cache["a"] == 1
    assert cache["c"] == 3
    cache["d"] = 4
    assert "a" not in cache


def test_lru_cache_get():
    cache = LRUCache(2)
    cache["a"] = 1
    cache["b"] = 2
    assert cache.get("a") == 1
    cache["c"] = 3
    assert cache.get("b") is None
    assert cache.get("a") == 1
    assert cache.get("c") == 3
    cache["d"] = 4
    assert cache.get("a") is None


def test_lru_cache_clear():
    cache = LRUCache(2)
    cache["a"] = 1
    cache["b"] = 2
    cache.clear()
    assert "a" not in cache
    assert "b" not in cache


def test_lru_cache_unlimited_size():
    cache = LRUCache()  # Unlimited size
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3
    assert cache["a"] == 1
    assert cache["b"] == 2
    assert cache["c"] == 3


def test_lru_cache_set_existing_key():
    cache = LRUCache(2)
    cache["a"] = 1
    cache["b"] = 2
    cache["a"] = 3  # Update existing key
    assert cache["a"] == 3
    cache["c"] = 4
    assert "b" not in cache  # b should be evicted


def test_lru_property():
    cache = LRUCache(3)
    cache["a"] = 1
    cache["b"] = 2
    cache["c"] = 3
    assert cache.lru == ["c", "b", "a"]
    cache["a"] = 4  # Accessing 'a' moves it to the end
    assert cache.lru == ["a", "c", "b"]



def test_length_property():
    cache = LRUCache(3)
    assert cache.length == 0
    cache["a"] = 1
    assert cache.length == 1
    cache["b"] = 2
    assert cache.length == 2
    cache["c"] = 3
    assert cache.length == 3
    cache["d"] = 4  # Evicts an element
    assert cache.length == 3

def test_contains():
    cache = LRUCache(2)
    cache["a"] = 1
    assert "a" in cache
    assert "b" not in cache


def test_delete():
    cache = LRUCache(2)
    cache["a"] = 1
    cache["b"] = 2
    del cache["a"]
    assert "a" not in cache
    assert cache["b"] == 2


def test_iterate():
    cache = LRUCache(2)
    cache["a"] = 1
    cache["b"] = 2
    assert list(cache) == ["b", "a"]

def test_get_default():
    cache = LRUCache(2)
    cache["a"] = 1
    assert cache.get("b", 2) == 2  # "b" not present, default value returned
    assert cache.get("a", 3) == 1 # "a" present



# === Tests for `FrozenDict` ===
import pytest

from tinydb.utils import FrozenDict


def test_frozendict_creation():
    # Test creating FrozenDict from dict
    data = {'a': 1, 'b': 2}
    frozen = FrozenDict(data)
    assert frozen == data
    assert isinstance(frozen, FrozenDict)

    # Test creating FrozenDict from keyword arguments
    frozen = FrozenDict(a=1, b=2)
    assert frozen == data
    assert isinstance(frozen, FrozenDict)

    # Test creating FrozenDict from iterable of tuples
    frozen = FrozenDict([('a', 1), ('b', 2)])
    assert frozen == data
    assert isinstance(frozen, FrozenDict)


def test_frozendict_immutability():
    frozen = FrozenDict({'a': 1})

    with pytest.raises(TypeError):
        frozen['a'] = 2

    with pytest.raises(TypeError):
        del frozen['a']

    with pytest.raises(TypeError):
        frozen.clear()

    with pytest.raises(TypeError):
        frozen.setdefault('b', 2)

    with pytest.raises(TypeError):
        frozen.popitem()

    with pytest.raises(TypeError):
        frozen.update({'b': 2})

    with pytest.raises(TypeError):
        frozen.pop('a')


def test_frozendict_hash():
    data1 = {'a': 1, 'b': 2}
    data2 = {'b': 2, 'a': 1}  # Different order, same hash

    frozen1 = FrozenDict(data1)
    frozen2 = FrozenDict(data2)

    assert hash(frozen1) == hash(frozen2)

    data3 = {'a': 1, 'b': 3}
    frozen3 = FrozenDict(data3)

    assert hash(frozen1) != hash(frozen3)


def test_frozendict_equality():
    data1 = {'a': 1, 'b': 2}
    data2 = {'b': 2, 'a': 1}

    frozen1 = FrozenDict(data1)
    frozen2 = FrozenDict(data2)

    assert frozen1 == data1
    assert frozen1 == data2
    assert frozen1 == frozen2

    data3 = {'a': 1, 'b': 3}
    frozen3 = FrozenDict(data3)

    assert frozen1 != data3
    assert frozen1 != frozen3


def test_frozendict_contains():
    frozen = FrozenDict({'a': 1, 'b': 2})

    assert 'a' in frozen
    assert 'b' in frozen
    assert 'c' not in frozen

def test_frozendict_get():
    frozen = FrozenDict({'a': 1, 'b': 2})
    assert frozen.get('a') == 1
    assert frozen.get('c', 3) == 3


def test_frozendict_iteration():
    data = {'a': 1, 'b': 2, 'c': 3}
    frozen = FrozenDict(data)

    assert list(frozen) == list(data)
    assert list(frozen.keys()) == list(data.keys())
    assert list(frozen.values()) == list(data.values())
    assert list(frozen.items()) == list(data.items())

    for key in frozen:
        assert key in data

    for key, value in frozen.items():
        assert data[key] == value

def test_frozendict_len():
    data = {'a': 1, 'b': 2, 'c': 3}
    frozen = FrozenDict(data)
    assert len(frozen) == len(data)


def test_frozendict_copy():
    data = {'a': 1, 'b': 2, 'c': 3}
    frozen = FrozenDict(data)
    copied = frozen.copy()
    assert isinstance(copied, FrozenDict)
    assert copied == frozen


# === Tests for `freeze` ===
import pytest
from tinydb.utils import freeze
from tinydb.utils import FrozenDict

@pytest.mark.parametrize('obj, frozen_obj', [
    (1, 1),
    ('test', 'test'),
    (3.14, 3.14),
    (None, None),
    (True, True),
    ({'a': 1, 'b': [1, 2, 3]}, FrozenDict({'a': 1, 'b': (1, 2, 3)})),
    ([1, 2, 3, {'a': 1}], (1, 2, 3, FrozenDict({'a': 1}))),
    ([1, 2, [3, 4]], (1, 2, (3, 4))),
    ({1, 2, 3}, frozenset({1, 2, 3})),
    ([1, 2, {3, 4}], (1, 2, frozenset({3, 4}))),
    ({'a': {'b': 1}, 'c': [1, {'d': 2}]}, FrozenDict({'a': FrozenDict({'b': 1}), 'c': (1, FrozenDict({'d': 2}))})),
    ((1, 2), (1, 2)) # Tuples are already immutable
])
def test_freeze(obj, frozen_obj):
    assert freeze(obj) == frozen_obj


def test_freeze_custom_object():
    class CustomObject:
        pass

    obj = CustomObject()
    assert freeze(obj) is obj  # Should return the same object


def test_freeze_recursive_list():
    obj = []
    obj.append(obj)  # create a self-referencing list

    with pytest.raises(RecursionError):
        freeze(obj)


def test_freeze_recursive_dict():
    obj = {}
    obj['a'] = obj  # create a self-referencing dict

    frozen_obj = freeze(obj)

    # Expecting a FrozenDict containing itself under 'a'
    assert isinstance(frozen_obj, FrozenDict)
    assert frozen_obj['a'] is frozen_obj