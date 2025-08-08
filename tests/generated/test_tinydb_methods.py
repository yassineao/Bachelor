# === Tests for `table` ===

import pytest
from tinydb import TinyDB, Storage
from tinydb.table import Table


@pytest.fixture
def mock_storage(mocker):
    return mocker.MagicMock(spec=Storage)


@pytest.fixture
def tinydb(mock_storage):
    db = TinyDB(storage=mock_storage)
    db.table_class = mocker.MagicMock(spec=Table)
    return db


def test_table_existing(tinydb, mocker):
    name = "table1"
    existing_table = mocker.MagicMock(spec=Table)
    tinydb._tables[name] = existing_table

    table = tinydb.table(name)

    assert table == existing_table
    tinydb.table_class.assert_not_called()


def test_table_new(tinydb, mock_storage):
    name = "table2"
    kwargs = {"cache_size": 5}

    table = tinydb.table(name, **kwargs)

    tinydb.table_class.assert_called_once_with(mock_storage, name, **kwargs)
    assert table == tinydb.table_class.return_value
    assert tinydb._tables[name] == table


def test_table_empty_name(tinydb, mock_storage):
    name = ""

    table = tinydb.table(name)

    tinydb.table_class.assert_called_once_with(mock_storage, name)
    assert table == tinydb.table_class.return_value
    assert tinydb._tables[name] == table


def test_table_special_chars_name(tinydb, mock_storage):
    name = "table.with.dots"

    table = tinydb.table(name)

    tinydb.table_class.assert_called_once_with(mock_storage, name)
    assert table == tinydb.table_class.return_value
    assert tinydb._tables[name] == table



# === Tests for `tables` ===

import pytest
from tinydb import TinyDB, Storage

def test_tables_empty_db(mocker):
    mock_storage = mocker.Mock(spec=Storage)
    mock_storage.read.return_value = None
    db = TinyDB(storage=mock_storage)
    assert db.tables() == set()
    db.close()

def test_tables_single_table(mocker):
    mock_storage = mocker.Mock(spec=Storage)
    mock_storage.read.return_value = {'_default': {0: {'test': 'data'}}}
    db = TinyDB(storage=mock_storage)
    assert db.tables() == {'_default'}
    db.close()

def test_tables_multiple_tables(mocker):
    mock_storage = mocker.Mock(spec=Storage)
    mock_storage.read.return_value = {'_default': {0: {'test': 'data'}}, 'table1': {1: {'test': 'data1'}}, 'table2': {}}
    db = TinyDB(storage=mock_storage)
    assert db.tables() == {'_default', 'table1', 'table2'}
    db.close()

def test_tables_non_dict_data(mocker):
    mock_storage = mocker.Mock(spec=Storage)
    mock_storage.read.return_value = [1, 2, 3]  # Invalid data type
    db = TinyDB(storage=mock_storage)
    assert db.tables() == set()
    db.close()




# === Tests for `drop_tables` ===

import pytest
from tinydb import TinyDB, table


@pytest.fixture
def mock_storage(mocker):
    return mocker.MagicMock()


@pytest.fixture
def table(mock_storage):
    db = TinyDB(storage=mock_storage)
    return db.table('test_table')


def test_drop_tables(table, mock_storage):
    table._tables['table1'] = 'mock_table1'
    table._tables['table2'] = 'mock_table2'

    table.drop_tables()

    mock_storage.write.assert_called_once_with({})
    assert table._tables == {}



def test_drop_tables_empty_tables(table, mock_storage):
    table.drop_tables()

    mock_storage.write.assert_called_once_with({})
    assert table._tables == {}

def test_drop_tables_storage_exception(table, mock_storage):
    mock_storage.write.side_effect = Exception("Storage write failed")
    
    with pytest.raises(Exception) as e:
        table.drop_tables()

    assert str(e.value) == "Storage write failed"



# === Tests for `drop_table` ===

import pytest
from tinydb import Storage, TinyDB
from tinydb.table import Table


@pytest.fixture
def mock_storage(mocker):
    return mocker.Mock(spec=Storage)


@pytest.fixture
def table(mock_storage):
    return Table(name='test_table', storage=mock_storage)


def test_drop_table_existing(table, mock_storage):
    mock_storage.read.return_value = {'test_table': {}}
    table._tables['test_table'] = 'mock_table_instance'

    table.drop_table('test_table')

    mock_storage.write.assert_called_once_with({})
    assert 'test_table' not in table._tables


def test_drop_table_nonexistent(table, mock_storage):
    mock_storage.read.return_value = {'other_table': {}}

    table.drop_table('test_table')

    mock_storage.write.assert_not_called()
    assert 'test_table' not in table._tables


def test_drop_table_uninitialized(table, mock_storage):
    mock_storage.read.return_value = None

    table.drop_table('test_table')

    mock_storage.write.assert_not_called()
    assert 'test_table' not in table._tables


def test_drop_table_multiple_tables(table, mock_storage):
    mock_storage.read.return_value = {'test_table': {}, 'other_table': {}}
    table._tables['test_table'] = 'mock_table_instance'

    table.drop_table('test_table')

    mock_storage.write.assert_called_once_with({'other_table': {}})
    assert 'test_table' not in table._tables


def test_drop_table_already_dropped_locally(table, mock_storage):
    mock_storage.read.return_value = {'test_table': {}}
    
    table.drop_table('test_table')
    
    mock_storage.write.assert_called_once_with({})
    assert 'test_table' not in table._tables


# === Tests for `storage` ===

import pytest
from tinydb.storages import Storage
from tinydb.table import Table


def test_storage():
    mock_storage = Storage()  # or a mock object
    table = Table(storage=mock_storage)
    assert table.storage() is mock_storage


def test_storage_none():
    with pytest.raises(TypeError):
        Table(storage=None)


# === Tests for `close` ===

import pytest
from tinydb.storages import Storage
from tinydb.table import Table


def test_close_calls_storage_close(mocker):
    mock_storage = mocker.MagicMock(spec=Storage)
    table = Table(mock_storage)
    table.close()
    mock_storage.close.assert_called_once()


def test_close_sets_opened_to_false(mocker):
    mock_storage = mocker.MagicMock(spec=Storage)
    table = Table(mock_storage)
    table.close()
    assert table._opened is False


def test_close_with_exception_in_storage_close(mocker):
    mock_storage = mocker.MagicMock(spec=Storage)
    mock_storage.close.side_effect = ValueError("Storage close failed")
    table = Table(mock_storage)
    with pytest.raises(ValueError):
        table.close()
    assert table._opened is False  # Ensure _opened is set even with an exception


