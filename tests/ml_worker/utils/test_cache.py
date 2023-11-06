from multiprocessing import get_context
from multiprocessing.context import SpawnContext
from multiprocessing.managers import SyncManager

import pytest

from giskard.ml_worker.utils.cache import SimpleCache


@pytest.fixture(scope="function")
def push_lru_cache() -> SimpleCache:
    cache = SimpleCache(max_results=2)
    cache.start({}, [])
    return cache


@pytest.fixture(scope="function")
def sync_push_lru_cache() -> SimpleCache:
    mp_context: SpawnContext = get_context("spawn")

    manager: SyncManager = mp_context.Manager()
    cache = SimpleCache(max_results=2)
    cache.start(manager.dict(), manager.list())
    yield cache
    manager.shutdown()


def test_key_should_be_str(push_lru_cache: SimpleCache):
    with pytest.raises(ValueError):
        push_lru_cache._generate_key({})


def test_add_result(push_lru_cache: SimpleCache):
    push_lru_cache.add_result("key1", "value1")
    assert push_lru_cache.get_result("key1") == (True, "value1")


def test_add_result_overflow(push_lru_cache: SimpleCache):
    push_lru_cache.add_result("key1", "value1")
    push_lru_cache.add_result("key2", "value2")
    assert len(push_lru_cache._keys) == 2
    assert len(push_lru_cache._results) == 2
    assert push_lru_cache._max_results == 2
    push_lru_cache.add_result("key3", "value3")  # This should remove "key1"
    assert push_lru_cache.get_result("key1") == (False, None)
    assert len(push_lru_cache._keys) == 2
    assert len(push_lru_cache._results) == 2


def test_get_result_not_found(push_lru_cache: SimpleCache):
    result = push_lru_cache.get_result("non_existing_key")
    assert result == (False, None)


def test_lru_behaviour(push_lru_cache: SimpleCache):
    push_lru_cache.add_result("key1", "value1")
    push_lru_cache.add_result("key2", "value2")
    did_match, result = push_lru_cache.get_result("key1")  # Key1 should become the most recently used
    assert did_match
    assert result == "value1"
    assert push_lru_cache._generate_key("key1") == push_lru_cache._keys[0]
    assert push_lru_cache._generate_key("key2") in push_lru_cache._keys
    push_lru_cache.add_result("key3", "value3")  # This should remove "key2"
    assert push_lru_cache.get_result("key2") == (False, None)
