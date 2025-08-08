# === Tests for `get_dynamic_class_hook` ===

import pytest
from typing import Any, Callable, Optional, Union, cast

from tinydb.storages import MemoryStorage, Storage
from tinydb.table import Table, Document
from mypy.nodes import TypeInfo, SymbolTableNode
from mypy.plugin import DynamicClassDefContext, Plugin
from mypy.types import Instance

class MockStorage(Storage):
    def __init__(self):
        self.data = {}

    def read(self):
        return self.data

    def write(self, data):
        self.data = data

    def close(self):
        pass


def test_get_dynamic_class_hook_match():
    table = Table(storage=MockStorage())
    hook = table.get_dynamic_class_hook('tinydb.utils.with_typehint')
    assert hook is not None

    class MockContext:
        def __init__(self):
             self.call = MockCall()
             self.api = MockApi()
             self.name = "test_name"

    class MockCall:
        def __init__(self):
            self.args = [MockNameExpr("test.Type")]

    class MockNameExpr:
        def __init__(self, fullname):
            self.fullname = fullname

    class MockApi:
        def __init__(self):
            self.added_node = None

        def add_symbol_table_node(self, name, node):
            self.added_node = node


    ctx = MockContext()
    table.lookup_fully_qualified = lambda x: x  # type: ignore
    hook(ctx)
    assert ctx.api.added_node == "test.Type"


def test_get_dynamic_class_hook_no_match():
    table = Table(storage=MockStorage())
    hook = table.get_dynamic_class_hook('other.name')
    assert hook is None


def test_get_dynamic_class_hook_lookup_fails():
    table = Table(storage=MockStorage())
    hook = table.get_dynamic_class_hook('tinydb.utils.with_typehint')
    assert hook is not None

    class MockContext:
        def __init__(self):
             self.call = MockCall()
             self.api = MockApi()


    class MockCall:
        def __init__(self):
            self.args = [MockNameExpr("test.Type")]


    class MockNameExpr:
        def __init__(self, fullname):
            self.fullname = fullname


    class MockApi:
        def __init__(self):
            self.added_node = None

        def add_symbol_table_node(self, name, node):
            self.added_node = node

    ctx = MockContext()
    table.lookup_fully_qualified = lambda x: None # type: ignore
    with pytest.raises(AssertionError):
        hook(ctx)


def test_get_dynamic_class_hook_no_fullname():
    table = Table(storage=MockStorage())
    hook = table.get_dynamic_class_hook('tinydb.utils.with_typehint')
    assert hook is not None

    class MockContext:
        def __init__(self):
             self.call = MockCall()
             self.api = MockApi()

    class MockCall:
        def __init__(self):
            self.args = [MockNameExpr(None)]

    class MockNameExpr:
        def __init__(self, fullname):
            self.fullname = fullname

    class MockApi:
        def add_symbol_table_node(self, name, node):
            pass

    ctx = MockContext()

    with pytest.raises(AssertionError):
        hook(ctx)

