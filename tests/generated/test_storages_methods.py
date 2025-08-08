# === Tests for `read` ===

import pytest
from tinydb.storages import Storage
from tinydb import TinyDB
import json
from typing import Dict, Any, Optional, cast

class MockStorage(Storage):
    def __init__(self):
        self.data: Optional[Dict[str, Dict[str, Any]]] = None

    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        return self.data

    def write(self, data: Dict[str, Dict[str, Any]]):
        self.data = data

    def close(self):
        pass


def test_read_empty():
    storage = MockStorage()
    assert storage.read() is None


def test_read_data():
    storage = MockStorage()
    data = {'_default': {'1': {'name': 'John'}}}
    storage.write(data)
    assert storage.read() == data

def test_read_after_write_json(tmpdir):
    path = str(tmpdir.join('test.json'))
    db = TinyDB(path, storage=JSONStorage)
    data = {'_default': {'1': {'name': 'John'}}}
    db.insert({'name': 'John'})
    db.close()

    storage = JSONStorage(path)
    read_data = storage.read()
    assert read_data == data
    storage.close()

def test_json_read_empty_file(tmpdir):
    path = str(tmpdir.join('test.json'))
    with open(path, 'w') as f:
        f.write('')  # Create empty file

    storage = JSONStorage(path)
    assert storage.read() == {}  # Should return empty dict for an empty JSON file
    storage.close()

def test_json_read_invalid_json(tmpdir):
    path = str(tmpdir.join('test.json'))
    with open(path, 'w') as f:
        f.write('invalid json')

    storage = JSONStorage(path)
    with pytest.raises(json.JSONDecodeError):
        storage.read()
    storage.close()



# === Tests for `write` ===
import pytest
from tinydb.storages import Storage, MemoryStorage
from typing import Dict, Any

class TestStorageWrite:

    def test_memory_storage_write(self):
        storage = MemoryStorage()
        data = {'_default': {1: {'name': 'test'}}}
        storage.write(data)
        assert storage.read() == data

    def test_failing_storage_write(self):
        class FailingStorage(Storage):
            def write(self, data: Dict[str, Dict[str, Any]]) -> None:
                raise IOError("Failed to write")

        storage = FailingStorage()
        data = {'_default': {1: {'name': 'test'}}}
        with pytest.raises(IOError):
            storage.write(data)



    def test_json_storage_write_read_roundtrip(self, tmp_path):
        from tinydb.storages import JSONStorage

        filepath = tmp_path / "test.json"
        storage = JSONStorage(filepath)
        data = {'_default': {1: {'name': 'test'}}}

        storage.write(data)

        read_data = storage.read()
        assert read_data == data

        storage.close()


    def test_yaml_storage_write_read_roundtrip(self, tmp_path):
        try:
            from tinydb.storages import YAMLStorage
        except ImportError:
            pytest.skip("YAMLStorage requires the 'yaml' package")


        filepath = tmp_path / "test.yaml"
        storage = YAMLStorage(filepath)
        data = {'_default': {1: {'name': 'test'}}}

        storage.write(data)

        read_data = storage.read()
        assert read_data == data

        storage.close()



# === Tests for `close` ===
import pytest
from tinydb.storages import Storage, MemoryStorage, JSONStorage


class CloseableStorage(Storage):
    def __init__(self):
        self.closed = False

    def close(self):
        self.closed = True


def test_memory_storage_close():
    storage = MemoryStorage()
    storage.close()  # No-op, should not raise any error


def test_json_storage_close_tempfile(tmpdir):
    temp_file = tmpdir.join("test.json")
    storage = JSONStorage(str(temp_file))
    storage.close()
    assert not temp_file.exists()  # JSONStorage cleans up after close() with delete=True default


def test_json_storage_close_no_delete(tmpdir):
    temp_file = tmpdir.join("test.json")
    storage = JSONStorage(str(temp_file), delete=False)
    storage.close()
    assert temp_file.exists()


def test_custom_close_implementation():
    storage = CloseableStorage()
    assert not storage.closed
    storage.close()
    assert storage.closed


def test_close_multiple_times():
    storage = CloseableStorage()
    storage.close()
    storage.close() # Should not raise an error
    assert storage.closed


# === Tests for `close` ===
import io
import json
from typing import Any, Dict

import pytest
from tinydb.storages import JSONStorage


def test_close_closes_file():
    mock_file = io.StringIO()
    storage = JSONStorage(mock_file)
    storage.close()
    assert mock_file.closed


def test_close_idempotent():
    mock_file = io.StringIO()
    storage = JSONStorage(mock_file)
    storage.close()
    storage.close()  # Should not raise an exception


def test_close_after_write():
    mock_file = io.StringIO()
    storage = JSONStorage(mock_file)
    storage.write({'key': 'value'})
    storage.close()
    assert mock_file.closed
    assert mock_file.getvalue() == '{"key": "value"}'


def test_close_with_empty_data():
    mock_file = io.StringIO()
    storage = JSONStorage(mock_file)
    storage.write({}) # Ensure file is created even with empty data
    storage.close()
    assert mock_file.closed
    assert mock_file.getvalue() == '{}'



def test_close_with_path():
    with pytest.raises(AttributeError):
        storage = JSONStorage('/tmp/nonexistent.json')  # Use a path that likely doesn't exist to avoid potential data loss in tests
        storage.close()


# === Tests for `read` ===
import json
import os
from typing import Any, Dict, Optional
from unittest.mock import Mock

import pytest

from tinydb.storages import JSONStorage


def test_read_empty_file():
    mock_handle = Mock()
    mock_handle.tell.return_value = 0
    storage = JSONStorage(mock_handle)
    assert storage.read() is None


def test_read_non_empty_file():
    mock_handle = Mock()
    mock_handle.tell.return_value = 10  # Non-zero size
    mock_handle.seek.return_value = None
    expected_data = {"test": "data"}
    mock_handle.read.return_value = json.dumps(expected_data).encode()  # Simulate reading JSON data

    storage = JSONStorage(mock_handle)

    assert storage.read() == expected_data




def test_read_with_tempfile(tmpdir):
    filepath = str(tmpdir.join('test.json'))
    data = {"test": "data"}
    with open(filepath, 'w') as f:
        json.dump(data, f)

    with open(filepath, 'r') as handle:
        storage = JSONStorage(handle)
        assert storage.read() == data


def test_read_invalid_json_with_tempfile(tmpdir):
    filepath = str(tmpdir.join('test.json'))
    with open(filepath, 'w') as f:
        f.write("invalid json")

    with open(filepath, 'r') as handle:
        storage = JSONStorage(handle)
        with pytest.raises(json.JSONDecodeError):
            storage.read()


# === Tests for `write` ===
import io
import json
import os
import pytest
from tinydb.storages import JSONStorage
from tempfile import NamedTemporaryFile
from unittest.mock import mock_open, patch


def test_jsonstorage_write_success():
    with NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
        storage = JSONStorage(tmpfile.name)
        data = {"_default": {"1": {"name": "test"}}}
        storage.write(data)
        tmpfile.seek(0)
        assert json.load(tmpfile) == data
    os.remove(tmpfile.name)


def test_jsonstorage_write_ioerror():
    mock_file = mock_open()
    mock_file.return_value.write.side_effect = io.UnsupportedOperation
    with patch("tinydb.storages.open", mock_file):
        with pytest.raises(IOError):
             storage = JSONStorage("")
             storage.write({"": {}})


def test_jsonstorage_write_kwargs():
    with NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
        storage = JSONStorage(tmpfile.name, indent=4)
        data = {"_default": {"1": {"name": "test"}}}
        storage.write(data)
        tmpfile.seek(0)
        written_data = tmpfile.read()
        assert json.loads(written_data) == data
        assert "    \"name\": \"test\"" in written_data  # Check for indentation
    os.remove(tmpfile.name)


def test_jsonstorage_write_truncate():
    with NamedTemporaryFile(mode="w+", delete=False) as tmpfile:
        tmpfile.write("initial longer data")
        tmpfile.flush()
        storage = JSONStorage(tmpfile.name)
        data = {"_default": {}}
        storage.write(data)
        tmpfile.seek(0)
        assert json.load(tmpfile) == data
        assert len(tmpfile.read()) == len(json.dumps(data))  # Ensure truncated
    os.remove(tmpfile.name)


# === Tests for `read` ===
import pytest
from tinydb.storages import MemoryStorage
from typing import Dict, Any, Optional


def test_memory_storage_read_empty():
    storage = MemoryStorage()
    assert storage.read() == {}

def test_memory_storage_read_with_data():
    expected_data = {'_default': {'1': {'name': 'John Doe'}}}
    storage = MemoryStorage()
    storage.memory = expected_data
    assert storage.read() == expected_data

def test_memory_storage_read_after_write():
    storage = MemoryStorage()
    data = {'_default': {'1': {'name': 'Jane Doe'}}}
    storage.write(data)
    assert storage.read() == data

def test_memory_storage_read_after_close_empty():
    storage = MemoryStorage()
    storage.close()
    assert storage.read() == {}


def test_memory_storage_read_after_close_with_data():
    expected_data = {'_default': {'1': {'name': 'John Doe'}}}
    storage = MemoryStorage()
    storage.memory = expected_data
    storage.close()
    assert storage.read() == expected_data


def test_memory_storage_read_type_hint():
    storage = MemoryStorage()
    data: Optional[Dict[str, Dict[str, Any]]] = storage.read()
    assert isinstance(data, dict) or data is None


# === Tests for `write` ===
import pytest
from tinydb.storages import MemoryStorage
from typing import Dict, Any

def test_memory_storage_write():
    storage = MemoryStorage()
    data = {'_default': {'1': {'name': 'John Doe'}}}
    storage.write(data)
    assert storage.memory == data

def test_memory_storage_write_empty():
    storage = MemoryStorage()
    data = {}
    storage.write(data)
    assert storage.memory == data

def test_memory_storage_write_none():
    storage = MemoryStorage()
    data = None
    with pytest.raises(TypeError):
        storage.write(data) # type: ignore[arg-type]

def test_memory_storage_write_invalid_data():
    storage = MemoryStorage()
    data: Dict[str, Dict[str, Any]] = {'_default': 'invalid'} # type: ignore[dict-item]
    with pytest.raises(TypeError):
        storage.write(data)


def test_memory_storage_write_multiple():
    storage = MemoryStorage()
    data1 = {'_default': {'1': {'name': 'John Doe'}}}
    data2 = {'_default': {'2': {'name': 'Jane Doe'}}}
    storage.write(data1)
    assert storage.memory == data1
    storage.write(data2)
    assert storage.memory == data2


def test_memory_storage_write_complex_data():
    storage = MemoryStorage()
    data = {
        '_default': {
            '1': {'name': 'John Doe', 'age': 30, 'active': True},
            '2': {'name': 'Jane Doe', 'age': 25, 'active': False},
        },
        'users': {
            '1': {'username': 'johndoe'},
            '2': {'username': 'janedoe'},
        }
    }
    storage.write(data)
    assert storage.memory == data
