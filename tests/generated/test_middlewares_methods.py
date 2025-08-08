# === Tests for `Middleware` ===

from tinydb.storages import MemoryStorage
from tinydb.middlewares import Middleware

import pytest


def test_middleware_initialization():
    middleware = Middleware(MemoryStorage)
    assert middleware._storage_cls == MemoryStorage
    assert middleware.storage is None


def test_middleware_call():
    middleware = Middleware(MemoryStorage)
    storage_instance = middleware()
    assert isinstance(storage_instance.storage, MemoryStorage)
    assert middleware.storage == storage_instance.storage


def test_middleware_nested():
    class MiddlewareA(Middleware):
        pass

    class MiddlewareB(Middleware):
        pass

    middleware_a = MiddlewareA(MiddlewareB(MemoryStorage))
    storage_instance = middleware_a('a', b='c')

    assert isinstance(storage_instance.storage, MiddlewareB)
    assert isinstance(storage_instance.storage.storage, MemoryStorage)

    assert storage_instance.storage._storage_cls == MemoryStorage

    # Check that the arguments are passed down correctly
    assert storage_instance.storage.storage._storage == {'a': 'a', 'b': 'c'}


def test_middleware_attribute_forwarding():
    middleware = Middleware(MemoryStorage)()

    with pytest.raises(AttributeError):
        middleware.non_existent_attribute  # pylint: disable=pointless-statement

    middleware.storage.write({})
    assert middleware.read() == {}
    middleware.close()


# === Tests for `CachingMiddleware` ===
import pytest
from tinydb.middlewares import Middleware
from tinydb.storages import MemoryStorage


class CachingMiddleware(Middleware):  # Include provided implementation here

    #: The number of write operations to cache before writing to disc
    WRITE_CACHE_SIZE = 1000

    # ... (rest of the provided implementation)


@pytest.fixture
def caching_middleware():
    return CachingMiddleware(MemoryStorage())


def test_initial_read_empty(caching_middleware):
    assert caching_middleware.read() == {}


def test_write_and_read_cached(caching_middleware):
    data = {"key": "value"}
    caching_middleware.write(data)
    assert caching_middleware.read() == data


def test_multiple_writes_cached(caching_middleware):
    data1 = {"key1": "value1"}
    data2 = {"key2": "value2"}
    caching_middleware.write(data1)
    caching_middleware.write(data2)
    assert caching_middleware.read() == data2  # Latest write should be in cache


def test_flush_writes_to_storage(caching_middleware):
    data = {"key": "value"}
    caching_middleware.write(data)
    caching_middleware.flush()
    assert caching_middleware.storage.read() == data


def test_cache_size_flush(caching_middleware):
    caching_middleware.WRITE_CACHE_SIZE = 2  # Temporarily reduce cache size for testing
    data1 = {"key1": "value1"}
    data2 = {"key2": "value2"}
    caching_middleware.write(data1)
    assert caching_middleware.storage.read() == {} # Should not be written yet
    caching_middleware.write(data2)
    assert caching_middleware.storage.read() == data2  # Should be flushed now


def test_close_flushes(caching_middleware):
    data = {"key": "value"}
    caching_middleware.write(data)
    caching_middleware.close()
    assert caching_middleware.storage.read() == data


def test_close_calls_storage_close(mocker, caching_middleware):
    mock_storage_close = mocker.patch.object(caching_middleware.storage, 'close')
    caching_middleware.close()
    mock_storage_close.assert_called_once()


def test_multiple_flush_calls(caching_middleware):
    data = {"key": "value"}
    caching_middleware.write(data)
    caching_middleware.flush()
    caching_middleware.flush()  # Second flush shouldn't cause issues
    assert caching_middleware.storage.read() == data


def test_flush_empty_cache(caching_middleware):
    caching_middleware.flush()  # Flushing an empty cache shouldn't write anything
    assert caching_middleware.storage.read() == {}
