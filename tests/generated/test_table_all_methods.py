# === Tests for `name` ===

import pytest
from tinydb.table import Table


def test_table_name():
    mock_storage = object()  # Mock storage, not used in this method
    table = Table(mock_storage, "test_table")
    assert table.name() == "test_table"


def test_table_name_empty():
    mock_storage = object()
    table = Table(mock_storage, "")
    assert table.name() == ""


def test_table_name_unicode():
    mock_storage = object()
    table_name = "測試表格"  # Unicode table name
    table = Table(mock_storage, table_name)
    assert table.name() == table_name


def test_table_name_special_chars():
    mock_storage = object()
    table_name = "t@ble_n-ame.123"  # Table name with special characters
    table = Table(mock_storage, table_name)
    assert table.name() == table_name


def test_table_name_none():
    mock_storage = object()
    with pytest.raises(TypeError):
        Table(mock_storage, None)  # Type error for None


def test_table_name_int():
    mock_storage = object()
    with pytest.raises(TypeError):
        Table(mock_storage, 123) # Type error for int



# === Tests for `storage` ===
import pytest
from tinydb.storages import Storage
from tinydb.table import Table


def test_storage():
    mock_storage = Storage()
    table = Table(storage=mock_storage)
    assert table.storage() is mock_storage


def test_storage_none():
    with pytest.raises(TypeError):
        Table(storage=None)  # type: ignore


def test_storage_invalid_type():
    with pytest.raises(TypeError):
        Table(storage=object()) # type: ignore


def test_storage_after_reloading(tmpdir):
    path = str(tmpdir.join('db.json'))
    storage = Storage() # Using a dummy storage to avoid creating a file

    table = Table(storage=storage)
    assert table.storage() is storage

    table2 = Table(path=path, storage=storage)
    assert table2.storage() is storage


def test_storage_with_path_and_storage(tmpdir):
    path = str(tmpdir.join('db.json'))
    mock_storage = Storage()
    table = Table(path=path, storage=mock_storage)
    assert table.storage() is mock_storage



# === Tests for `insert` ===
import pytest
from tinydb import TinyDB, table
from typing import Mapping
from tinydb.table import Table, Document


@pytest.fixture
def mock_storage(mocker):
    return mocker.MagicMock()


@pytest.fixture
def table_instance(mock_storage):
    tbl = Table(mock_storage)
    tbl._next_id = 1
    return tbl


def test_insert_dict(table_instance, mock_storage):
    doc_id = table_instance.insert({'key': 'value'})
    assert doc_id == 1
    mock_storage._update_table.assert_called_once()
    updater = mock_storage._update_table.call_args[0][0]
    table_data = {}
    updater(table_data)
    assert table_data == {1: {'key': 'value'}}


def test_insert_document(table_instance, mock_storage):
    doc = Document({'key': 'value'}, doc_id=5)
    doc_id = table_instance.insert(doc)
    assert doc_id == 5
    assert table_instance._next_id is None
    mock_storage._update_table.assert_called_once()
    updater = mock_storage._update_table.call_args[0][0]
    table_data = {}
    updater(table_data)
    assert table_data == {5: {'key': 'value'}}


def test_insert_non_mapping(table_instance):
    with pytest.raises(ValueError) as excinfo:
        table_instance.insert([1, 2, 3])
    assert 'Document is not a Mapping' in str(excinfo.value)


def test_insert_duplicate(table_instance, mock_storage):
    mock_storage._update_table.side_effect = ValueError(
        'Document with ID 1 already exists')

    with pytest.raises(ValueError) as excinfo:
        table_instance.insert({'key': 'value'})
    
    assert 'Document with ID 1 already exists' in str(excinfo.value)



def test_insert_custom_mapping(table_instance, mock_storage):
    class CustomMapping(Mapping):
        def __init__(self, data):
            self._data = data

        def __getitem__(self, key):
            return self._data[key]

        def __iter__(self):
            return iter(self._data)

        def __len__(self):
            return len(self._data)

    doc_id = table_instance.insert(CustomMapping({'key': 'value'}))
    assert doc_id == 1
    mock_storage._update_table.assert_called_once()
    updater = mock_storage._update_table.call_args[0][0]
    table_data = {}
    updater(table_data)
    assert table_data == {1: {'key': 'value'}}



# === Tests for `insert_multiple` ===
import pytest
from tinydb import TinyDB, table
from tinydb.storages import MemoryStorage
from typing import Iterable, Mapping, List, Dict, Any
from unittest.mock import Mock


class Document(dict):
    def __init__(self, value, doc_id=None):
        super().__init__(value)
        self.doc_id = doc_id

class TestInsertMultiple:

    def test_insert_multiple_empty(self):
        storage_mock = Mock()
        tbl = table.Table(storage_mock)
        assert tbl.insert_multiple([]) == []
        storage_mock.write.assert_called_once_with({})

    def test_insert_multiple_simple(self):
        storage_mock = Mock()
        tbl = table.Table(storage_mock)
        assert tbl.insert_multiple([{'a': 1}, {'b': 2}]) == [1, 2]
        storage_mock.write.assert_called_once_with({1: {'a': 1}, 2: {'b': 2}})

    def test_insert_multiple_with_doc_id(self):
        storage_mock = Mock()
        tbl = table.Table(storage_mock, document_class=Document)
        docs = [Document({'a': 1}, doc_id=123), Document({'b': 2}, doc_id=456)]
        assert tbl.insert_multiple(docs) == [123, 456]
        storage_mock.write.assert_called_once_with({123: {'a': 1}, 456: {'b': 2}})


    def test_insert_multiple_with_existing_doc_id(self):
        storage_mock = Mock()
        storage_mock.read.return_value = {123: {'a': 1}}
        tbl = table.Table(storage_mock, document_class=Document)
        docs = [Document({'a': 1}, doc_id=123), Document({'b': 2}, doc_id=456)]

        with pytest.raises(ValueError) as excinfo:
            tbl.insert_multiple(docs)
        assert "Document with ID 123 already exists" in str(excinfo.value)


    def test_insert_multiple_non_mapping(self):
        storage_mock = Mock()
        tbl = table.Table(storage_mock)

        with pytest.raises(ValueError) as excinfo:
            tbl.insert_multiple([1, 2, 3])
        assert "Document is not a Mapping" in str(excinfo.value)

    def test_insert_multiple_mixed(self):
        storage_mock = Mock()
        tbl = table.Table(storage_mock, document_class=Document)
        docs = [Document({'a': 1}, doc_id=123), {'b': 2}]
        assert tbl.insert_multiple(docs) == [123, 1]
        storage_mock.write.assert_called_once_with({123: {'a': 1}, 1: {'b': 2}})


    def test_insert_multiple_with_initial_data(self):
        storage_mock = Mock()
        storage_mock.read.return_value = {1: {'a': 1}}
        tbl = table.Table(storage_mock)
        assert tbl.insert_multiple([{'b': 2}]) == [2]
        storage_mock.write.assert_called_once_with({1: {'a': 1}, 2: {'b': 2}})



# === Tests for `all` ===
import pytest
from tinydb.table import Table
from tinydb.storages import MemoryStorage


def test_table_all_empty():
    storage_mock = MemoryStorage()
    table = Table(storage=storage_mock)
    assert table.all() == []


def test_table_all_with_data():
    storage_mock = MemoryStorage()
    table = Table(storage=storage_mock)
    table.insert({'a': 1})
    table.insert({'b': 2})
    result = table.all()
    assert len(result) == 2
    assert {'a': 1} in result
    assert {'b': 2} in result


def test_table_all_after_clear():
    storage_mock = MemoryStorage()
    table = Table(storage=storage_mock)
    table.insert({'a': 1})
    table.clear()
    assert table.all() == []


def test_table_all_after_remove():
    storage_mock = MemoryStorage()
    table = Table(storage=storage_mock)
    table.insert({'a': 1})
    table.insert({'b': 2})
    table.remove(doc_ids=[1])
    result = table.all()
    assert len(result) == 1
    assert {'b': 2} in result
    

def test_table_all_after_update():
    storage_mock = MemoryStorage()
    table = Table(storage=storage_mock)
    table.insert({'a': 1})
    table.update({'a': 2})
    result = table.all()
    assert len(result) == 1
    assert {'a': 2} in result


def test_table_all_with_deleted_docs():
    storage_mock = MemoryStorage()
    table = Table(storage=storage_mock)
    table.insert({'a': 1})
    doc_id = table.insert({'b': 2})
    storage_mock.delete(doc_id)
    assert len(table.all()) == 1
    assert {'a': 1} in table.all()


# === Tests for `search` ===
import pytest
from tinydb import TinyDB, Query
from tinydb.table import Table, Document
from typing import List, Callable, Dict, Any
from unittest.mock import MagicMock


@pytest.fixture
def mock_table():
    table = Table(storage=MagicMock())
    table._read_table = MagicMock(return_value={1: {'a': 1}, 2: {'a': 2}, 3: {'a': 3}})
    table.document_class = MagicMock(side_effect=lambda doc, doc_id: doc)  # Return the doc itself
    table.document_id_class = MagicMock(side_effect=lambda doc_id: doc_id)
    table._query_cache = {}  # Initialize an empty cache for testing
    return table


def test_search_cache_hit(mock_table):
    cond = Query().a == 1
    mock_table._query_cache[cond] = [{'a': 1}]
    assert mock_table.search(cond) == [{'a': 1}]


def test_search_no_cache(mock_table):
    cond = Query().a == 2
    assert mock_table.search(cond) == [{'a': 2}]
    assert cond in mock_table._query_cache


def test_search_no_match(mock_table):
    cond = Query().a == 4
    assert mock_table.search(cond) == []
    assert cond in mock_table._query_cache


def test_search_multiple_matches(mock_table):
    cond = Query().a > 1
    assert mock_table.search(cond) == [{'a': 2}, {'a': 3}]
    assert cond in mock_table._query_cache


def test_search_custom_query_not_cacheable(mock_table):
    class NonCacheableQuery:
        def __call__(self, doc):
            return True

        def is_cacheable(self):
            return False

    cond = NonCacheableQuery()
    assert mock_table.search(cond) == [{'a': 1}, {'a': 2}, {'a': 3}]
    assert cond not in mock_table._query_cache


def test_search_custom_query_cacheable_by_default(mock_table):
    class CacheableByDefaultQuery:
        def __call__(self, doc):
            return True
    
    cond = CacheableByDefaultQuery()
    assert mock_table.search(cond) == [{'a': 1}, {'a': 2}, {'a': 3}]
    assert cond in mock_table._query_cache


def test_search_empty_table(mock_table):
    mock_table._read_table.return_value = {}
    cond = Query().a == 1
    assert mock_table.search(cond) == []
    assert cond in mock_table._query_cache

# === Tests for `get` ===
import pytest
from tinydb import TinyDB, Query
from tinydb.table import Table, Document
from typing import Optional, List, Union
from unittest.mock import MagicMock


@pytest.fixture
def mock_table():
    mock_storage = MagicMock()
    mock_storage.read.return_value = {}
    table = Table(mock_storage)
    return table


def test_get_by_doc_id(mock_table):
    mock_table._read_table = lambda: {'1': {'value': 'test'}}
    doc = mock_table.get(doc_id=1)
    assert doc == Document({'value': 'test'}, 1)


def test_get_by_doc_id_not_found(mock_table):
    mock_table._read_table = lambda: {'1': {'value': 'test'}}
    doc = mock_table.get(doc_id=2)
    assert doc is None


def test_get_by_doc_ids(mock_table):
    mock_table._read_table = lambda: {'1': {'a': 1}, '2': {'b': 2}, '3': {'c': 3}}
    docs = mock_table.get(doc_ids=[1, 3])
    assert docs == [Document({'a': 1}, 1), Document({'c': 3}, 3)]


def test_get_by_doc_ids_empty(mock_table):
    mock_table._read_table = lambda: {'1': {'a': 1}, '2': {'b': 2}, '3': {'c': 3}}
    docs = mock_table.get(doc_ids=[])
    assert docs == []



def test_get_by_doc_ids_not_found(mock_table):
    mock_table._read_table = lambda: {'1': {'a': 1}, '2': {'b': 2}, '3': {'c': 3}}
    docs = mock_table.get(doc_ids=[4, 5])
    assert docs == []



def test_get_by_query(mock_table):
    mock_table._read_table = lambda: {'1': {'value': 'test'}, '2': {'value': 'other'}}
    User = Query()
    doc = mock_table.get(User.value == 'test')
    assert doc == Document({'value': 'test'}, 1)


def test_get_by_query_not_found(mock_table):
    mock_table._read_table = lambda: {'1': {'value': 'test'}, '2': {'value': 'other'}}
    User = Query()
    doc = mock_table.get(User.value == 'not_found')
    assert doc is None


def test_get_no_arguments(mock_table):
    with pytest.raises(RuntimeError):
        mock_table.get()


def test_get_multiple_arguments(mock_table):
    with pytest.raises(TypeError): # TinyDB raises a TypeError if more than one of the arguments is supplied
        mock_table.get(doc_id=1, doc_ids=[1,2])

def test_get_by_doc_ids_string_ids(mock_table):
    mock_table._read_table = lambda: {'1': {'a': 1}, '2': {'b': 2}, '3': {'c': 3}}
    docs = mock_table.get(doc_ids=['1', '3'])
    assert docs == [Document({'a': 1}, 1), Document({'c': 3}, 3)]


def test_get_by_doc_id_string_id(mock_table):
    mock_table._read_table = lambda: {'1': {'value': 'test'}}
    doc = mock_table.get(doc_id='1')
    assert doc == Document({'value': 'test'}, 1)

# === Tests for `contains` ===
import pytest
from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage
from tinydb.table import Table


def test_contains_with_doc_id(monkeypatch):
    mock_storage = MemoryStorage()
    mock_storage.write({'1': {'_id': 1}, '2': {'_id': 2}})
    monkeypatch.setattr(Table, '_storage', mock_storage)

    table = Table(TinyDB(storage=MemoryStorage()))  # Dummy db for Table instantiation
    assert table.contains(doc_id=1)
    assert not table.contains(doc_id=3)


def test_contains_with_cond(monkeypatch):
    mock_storage = MemoryStorage()
    mock_storage.write({'1': {'a': 1}, '2': {'a': 2}})
    monkeypatch.setattr(Table, '_storage', mock_storage)

    table = Table(TinyDB(storage=MemoryStorage()))
    User = Query()
    assert table.contains(User.a == 1)
    assert not table.contains(User.a == 3)


def test_contains_with_both_doc_id_and_cond(monkeypatch):
    mock_storage = MemoryStorage()
    mock_storage.write({'1': {'_id': 1, 'a': 1}, '2': {'_id': 2, 'a': 2}})
    monkeypatch.setattr(Table, '_storage', mock_storage)

    table = Table(TinyDB(storage=MemoryStorage()))
    User = Query()
    assert table.contains(doc_id=1)  # doc_id takes precedence


def test_contains_with_no_arguments():
    table = Table(TinyDB(storage=MemoryStorage()))
    with pytest.raises(RuntimeError):
        table.contains()


def test_contains_with_empty_db_doc_id(monkeypatch):
    mock_storage = MemoryStorage()
    monkeypatch.setattr(Table, '_storage', mock_storage)
    table = Table(TinyDB(storage=MemoryStorage()))
    assert not table.contains(doc_id=1)


def test_contains_with_empty_db_cond(monkeypatch):
    mock_storage = MemoryStorage()
    monkeypatch.setattr(Table, '_storage', mock_storage)
    table = Table(TinyDB(storage=MemoryStorage()))
    User = Query()
    assert not table.contains(User.a == 1)


# === Tests for `update` ===
import pytest
from typing import Callable, Mapping, Optional, Iterable, List, Union, Any, cast
from tinydb.table import Table
from tinydb.queries import QueryLike


class MockStorage:
    def __init__(self):
        self.table = {}

    def read(self):
        return self.table

    def write(self, data):
        self.table = data



@pytest.fixture
def table():
    storage = MockStorage()
    return Table(storage)


def test_update_with_doc_ids(table: Table):
    table.insert_multiple([{'a': 1}, {'b': 2}, {'c': 3}])
    updated_ids = table.update({'a': 2}, doc_ids=[1, 3])
    assert updated_ids == [1, 3]
    assert table.all() == [{'a': 2}, {'b': 2}, {'a': 2}]


def test_update_with_callable_fields_and_doc_ids(table: Table):
    table.insert_multiple([{'a': 1}, {'b': 2}, {'c': 3}])

    def update_func(doc):
        doc['a'] = 2

    updated_ids = table.update(update_func, doc_ids=[1, 3])
    assert updated_ids == [1, 3]
    assert table.all() == [{'a': 2}, {'b': 2}, {'a': 2}]


def test_update_with_cond(table: Table):
    table.insert_multiple([{'a': 1}, {'b': 2}, {'a': 3}])
    updated_ids = table.update({'a': 4}, where(lambda doc: 'a' in doc))
    assert sorted(updated_ids) == [1, 3]
    assert table.all() == [{'a': 4}, {'b': 2}, {'a': 4}]


def test_update_with_cond_callable_fields(table: Table):
    table.insert_multiple([{'a': 1}, {'b': 2}, {'a': 3}])

    def update_func(doc):
        doc['a'] = 4
    
    updated_ids = table.update(update_func, where(lambda doc: 'a' in doc))
    assert sorted(updated_ids) == [1, 3]
    assert table.all() == [{'a': 4}, {'b': 2}, {'a': 4}]


def test_update_all(table: Table):
    table.insert_multiple([{'a': 1}, {'b': 2}])
    updated_ids = table.update({'c': 3})
    assert sorted(updated_ids) == [1, 2]
    assert table.all() == [{'a': 1, 'c': 3}, {'b': 2, 'c': 3}]


def test_update_all_callable_fields(table: Table):
    table.insert_multiple([{'a': 1}, {'b': 2}])

    def update_func(doc):
        doc['c'] = 3

    updated_ids = table.update(update_func)
    assert sorted(updated_ids) == [1, 2]
    assert table.all() == [{'a': 1, 'c': 3}, {'b': 2, 'c': 3}]


def test_update_empty_table(table: Table):
    updated_ids = table.update({'a': 1})
    assert updated_ids == []
    assert table.all() == []


def where(func) -> QueryLike:
    return lambda doc: func(doc)



# === Tests for `update_multiple` ===
import pytest
from typing import Callable, Iterable, List, Mapping, Tuple, Union, cast
from tinydb.table import Table
from tinydb.storages import MemoryStorage
from tinydb.queries import QueryLike, Query


class MockStorage:
    def __init__(self):
        self._table = {}

    def read(self):
        return self._table

    def write(self, data):
        self._table = data

    def close(self):
        pass


def test_update_multiple_empty_updates():
    table = Table(storage=MockStorage())
    assert table.update_multiple([]) == []


def test_update_multiple_single_update():
    table = Table(storage=MockStorage())
    table.insert({"a": 1, "b": 2})
    assert table.update_multiple([({"a": 2}, Query().a == 1)]) == [1]
    assert table.all() == [{"a": 2, "b": 2}]


def test_update_multiple_multiple_updates():
    table = Table(storage=MockStorage())
    table.insert({"a": 1, "b": 2})
    table.insert({"a": 1, "b": 3})
    assert table.update_multiple([({"a": 2}, Query().a == 1)]) == [1, 2]
    assert table.all() == [{"a": 2, "b": 2}, {"a": 2, "b": 3}]


def test_update_multiple_no_match():
    table = Table(storage=MockStorage())
    table.insert({"a": 1, "b": 2})
    assert table.update_multiple([({"a": 2}, Query().a == 2)]) == []
    assert table.all() == [{"a": 1, "b": 2}]


def test_update_multiple_callable():
    table = Table(storage=MockStorage())
    table.insert({"a": 1, "b": 2})
    assert table.update_multiple([(lambda doc: doc.update({"a": 2}), Query().a == 1)]) == [1]
    assert table.all() == [{"a": 2, "b": 2}]


def test_update_multiple_multiple_conditions():
    table = Table(storage=MockStorage())
    table.insert({"a": 1, "b": 2})
    table.insert({"a": 1, "b": 3})
    table.insert({"a": 2, "b": 2})
    assert table.update_multiple([({"a": 3}, Query().a == 1), ({"b": 4}, Query().b == 2)]) == [1, 2, 3]
    assert table.all() == [{"a": 3, "b": 4}, {"a": 3, "b": 3}, {"a": 2, "b": 4}]


def test_update_multiple_delete_during_update():
    table = Table(storage=MockStorage())
    table.insert({"a": 1})
    table.insert({"a": 1})
    table.insert({"a": 2})

    def update_and_delete(doc):
        doc.update({"b": 2})
        if doc["a"] == 1:
            table.remove(doc_ids=[doc.doc_id])


    assert table.update_multiple([(update_and_delete, Query().a.exists())]) == [1, 2, 3]
    assert table.all() == [{"a": 2, "b": 2}]


# === Tests for `upsert` ===
import pytest
from tinydb import TinyDB, table
from tinydb.storages import MemoryStorage
from typing import List, Mapping, Optional, Union

def test_upsert_with_doc_id():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    doc = tbl.document_class({'a': 1}, doc_id=1)
    assert tbl.upsert(doc) == [1]
    assert tbl.upsert({'b': 2}, doc_id=1) == [1]
    assert tbl.get(doc_id=1) == {'b': 2}

def test_upsert_with_cond():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    tbl.insert({'a': 1})
    assert tbl.upsert({'b': 2}, table.Query().a == 1) == [1]
    assert tbl.all() == [{'b': 2}]

def test_upsert_insert():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    assert tbl.upsert({'a': 1}) == [1]
    assert tbl.all() == [{'a': 1}]

def test_upsert_no_cond_no_doc_id():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    with pytest.raises(ValueError):
        tbl.upsert({'a': 1})

def test_upsert_missing_doc_id():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    doc = tbl.document_class({'a': 1}, doc_id=1)
    db.close()
    with pytest.raises(KeyError):
        tbl.upsert(doc)

def test_upsert_multiple_update():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    tbl.insert({'a': 1})
    tbl.insert({'a': 1})
    assert tbl.upsert({'b': 2}, table.Query().a == 1) == [1, 2]
    assert tbl.all() == [{'b': 2}, {'b': 2}]

def test_upsert_empty_table():
    db = TinyDB(storage=MemoryStorage)
    tbl = db.table('test')
    assert tbl.upsert({'a': 1}, table.Query().a == 1) == [1]
    assert tbl.all() == [{'a': 1}]



# === Tests for `remove` ===
import pytest
from tinydb import Query, TinyDB
from tinydb.table import Table
from typing import Any, Callable, Dict, Iterable, List, Optional, cast
from unittest import mock


@pytest.mark.parametrize('doc_ids, expected_removed_ids', [
    ([1, 2, 3], [1, 2, 3]),
    (iter([4, 5, 6]), [4, 5, 6]),
    ([], []),
])
def test_remove_by_doc_ids(doc_ids: Iterable[int], expected_removed_ids: List[int]) -> None:
    table = Table(mock.MagicMock())  # type: ignore[arg-type]
    table._update_table = mock.MagicMock()

    removed_ids = table.remove(doc_ids=doc_ids)

    assert removed_ids == expected_removed_ids
    table._update_table.assert_called_once()
    updater_func = table._update_table.call_args[0][0]

    test_table = {1: {}, 2: {}, 3: {}, 4: {}, 5: {}, 6: {}}
    updater_func(test_table)
    expected_table = {k: v for k, v in test_table.items() if k not in expected_removed_ids}
    assert test_table == expected_table


@pytest.mark.parametrize('cond, table_data, expected_removed_ids', [
    (Query().x == 1, {1: {'x': 1}, 2: {'x': 2}}, [1]),
    (Query().x > 1, {1: {'x': 1}, 2: {'x': 2}, 3: {'x': 3}}, [2, 3]),
    (Query().x == 1, {}, []),
])
def test_remove_by_cond(cond: Query, table_data: Dict[int, Dict], expected_removed_ids: List[int]) -> None:
    table = Table(mock.MagicMock())  # type: ignore[arg-type]
    table._update_table = mock.MagicMock()

    # We have to add dummy table data before running the test
    table._table = table_data.copy()


    removed_ids = table.remove(cond=cond)

    assert removed_ids == expected_removed_ids

    table._update_table.assert_called_once()
    updater_func = table._update_table.call_args[0][0]

    test_table = table_data.copy()
    updater_func(test_table)

    expected_table = {k: v for k, v in test_table.items() if k not in expected_removed_ids}

    assert test_table == expected_table


def test_remove_no_args() -> None:
    table = Table(mock.MagicMock())  # type: ignore[arg-type]
    with pytest.raises(RuntimeError):
        table.remove()


# === Tests for `truncate` ===
import pytest
from tinydb import TinyDB, where
from tinydb.storages import MemoryStorage


def test_truncate_empty_table():
    storage = MemoryStorage()
    db = TinyDB(storage=storage)
    table = db.table('test_table')
    table.truncate()
    assert len(table) == 0
    db.close()

def test_truncate_populated_table():
    storage = MemoryStorage()
    db = TinyDB(storage=storage)
    table = db.table('test_table')
    table.insert({'a': 1})
    table.insert({'b': 2})
    table.truncate()
    assert len(table) == 0
    db.close()

def test_truncate_resets_id():
    storage = MemoryStorage()
    db = TinyDB(storage=storage)
    table = db.table('test_table')
    table.insert({'a': 1})
    table.truncate()
    table.insert({'b': 2})
    assert table.get(where('b') == 2).doc_id == 1
    db.close()

def test_truncate_multiple_times():
    storage = MemoryStorage()
    db = TinyDB(storage=storage)
    table = db.table('test_table')
    table.insert({'a': 1})
    table.truncate()
    table.truncate()
    assert len(table) == 0
    db.close()


def test_truncate_after_all():
    storage = MemoryStorage()
    db = TinyDB(storage=storage)
    table = db.table('test_table')
    table.insert({'a': 1})
    table.insert({'b': 2})
    table.all() # Access all documents before truncate
    table.truncate()
    assert len(table) == 0
    db.close()

# === Tests for `count` ===
import pytest
from tinydb.table import Table
from tinydb.queries import Query
from tinydb.storages import MemoryStorage


def test_count_empty_table():
    storage = MemoryStorage()
    table = Table(storage)
    assert table.count(Query()._id == 1) == 0


def test_count_matching_documents():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert_multiple([{'i': 1}, {'i': 2}, {'i': 1}])
    assert table.count(Query().i == 1) == 2


def test_count_no_matching_documents():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert_multiple([{'i': 1}, {'i': 2}, {'i': 1}])
    assert table.count(Query().i == 3) == 0


def test_count_all_documents():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert_multiple([{'i': 1}, {'i': 2}, {'i': 1}])
    assert table.count(Query()) == 3  # Counts all documents


def test_count_complex_query():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert_multiple([{'i': 1, 'j': 'a'}, {'i': 2, 'j': 'b'}, {'i': 1, 'j': 'a'}])
    assert table.count((Query().i == 1) & (Query().j == 'a')) == 2


def test_count_with_invalid_query():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert({'i': 1})
    with pytest.raises(TypeError):
        table.count("invalid query")  # Type error expected


def test_count_with_mocked_search():
    storage = MemoryStorage()
    table = Table(storage)
    
    with pytest.raises(TypeError):
        table.count("invalid query")  # Type error expected


def test_count_with_none_query():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert({'i': 1})
    with pytest.raises(TypeError):  # Expecting TypeError for None query
        table.count(None)


def test_count_with_empty_query_after_clear():
    storage = MemoryStorage()
    table = Table(storage)
    table.insert({'i': 1})
    table.clear()  # Clear all documents
    assert table.count(Query()) == 0

# === Tests for `clear_cache` ===
import pytest
from tinydb.table import Table


@pytest.fixture
def mock_table():
    table = Table(None)  # Storage is irrelevant for this test
    table._query_cache = {'key1': 'value1', 'key2': 'value2'}
    return table


def test_clear_cache_clears_cache(mock_table):
    mock_table.clear_cache()
    assert len(mock_table._query_cache) == 0


def test_clear_cache_empty_cache(mock_table):
    mock_table._query_cache.clear()  # Start with empty cache
    mock_table.clear_cache()
    assert len(mock_table._query_cache) == 0


def test_clear_cache_no_errors_with_none_cache(monkeypatch):
    table = Table(None)
    monkeypatch.setattr(table, '_query_cache', None)  # Simulate a missing cache
    with pytest.raises(AttributeError): # Clearing a NoneType should raise an AttributeError 
        table.clear_cache()
