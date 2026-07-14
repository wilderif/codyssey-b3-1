"""Required behavior tests for the Mini Redis assignment."""

from mini_redis.cli.parser import execute_command
from mini_redis.core.store import MiniRedis


class FakeClock:
    """Controllable clock for TTL tests."""

    def __init__(self):
        """Start at time zero."""
        self.now = 0.0

    def __call__(self):
        """Return the current fake timestamp."""
        return self.now

    def advance(self, seconds):
        """Move fake time forward."""
        self.now += seconds


def run(store, line):
    """Execute a command line in tests."""
    return execute_command(store, line)


def test_string_commands_and_quoted_values():
    """SET, GET, EXISTS, DEL, DBSIZE, and KEYS follow Redis-style output."""
    store = MiniRedis()

    assert run(store, 'SET user:1 "Alice Smith"') == "OK"
    assert run(store, "GET user:1") == '"Alice Smith"'
    assert run(store, "EXISTS user:1") == "(integer) 1"
    assert run(store, "DBSIZE") == "(integer) 1"
    assert run(store, "KEYS") == '1. "user:1"'
    assert run(store, "DEL user:1") == "(integer) 1"
    assert run(store, "GET user:1") == "(nil)"
    assert run(store, "EXISTS user:1") == "(integer) 0"
    assert run(store, "DBSIZE") == "(integer) 0"
    assert run(store, "KEYS") == "(empty array)"


def test_lru_eviction_and_memory_info():
    """maxmemory evicts least recently used keys and updates accounting."""
    store = MiniRedis()

    assert run(store, "CONFIG SET maxmemory 30") == "OK"
    assert run(store, 'SET user:1 "Alice"') == "OK"
    assert run(store, 'SET user:2 "Bob"') == "OK"
    assert run(store, 'SET user:3 "Charlie"') == "OK"

    assert run(store, "GET user:1") == "(nil)"
    assert run(store, "GET user:2") == '"Bob"'
    assert run(store, "INFO memory") == "used_memory:22\nmaxmemory:30\nevicted_keys:1"


def test_get_updates_lru_order():
    """A successful GET makes that key most recently used."""
    store = MiniRedis()

    assert run(store, "CONFIG SET maxmemory 7") == "OK"
    assert run(store, "SET a 1") == "OK"
    assert run(store, "SET b 22") == "OK"
    assert run(store, "GET a") == '"1"'
    assert run(store, "SET c 333") == "OK"

    assert run(store, "GET a") == '"1"'
    assert run(store, "GET b") == "(nil)"
    assert run(store, "GET c") == '"333"'


def test_hash_map_resize_keeps_all_entries():
    """Hash map resize preserves existing keys and values."""
    store = MiniRedis()

    index = 0
    while index < 12:
        assert run(store, "SET key:" + str(index) + " value:" + str(index)) == "OK"
        index += 1

    assert run(store, "DBSIZE") == "(integer) 12"
    index = 0
    while index < 12:
        assert run(store, "GET key:" + str(index)) == '"value:' + str(index) + '"'
        index += 1


def test_single_entry_oom_does_not_store_value():
    """A single value larger than maxmemory is rejected."""
    store = MiniRedis()

    assert run(store, "CONFIG SET maxmemory 3") == "OK"
    assert run(store, "SET key value") == "(error) OOM command not allowed when used_memory > 'maxmemory'"
    assert run(store, "GET key") == "(nil)"
    assert run(store, "INFO memory") == "used_memory:0\nmaxmemory:3\nevicted_keys:0"


def test_ttl_expiration_and_overwrite_clears_ttl():
    """EXPIRE and TTL use heap-backed lazy expiration rules."""
    clock = FakeClock()
    store = MiniRedis(clock=clock)

    assert run(store, "SET session token") == "OK"
    assert run(store, "EXPIRE session 3") == "(integer) 1"
    clock.advance(1)
    assert run(store, "TTL session") == "(integer) 2"
    assert run(store, "SET session fresh") == "OK"
    assert run(store, "TTL session") == "(integer) -1"
    clock.advance(10)
    assert run(store, "GET session") == '"fresh"'


def test_reset_expire_leaves_stale_heap_items_harmless():
    """Old heap records do not delete a key after EXPIRE is reset."""
    clock = FakeClock()
    store = MiniRedis(clock=clock)

    assert run(store, "SET token alive") == "OK"
    assert run(store, "EXPIRE token 10") == "(integer) 1"
    clock.advance(1)
    assert run(store, "EXPIRE token 20") == "(integer) 1"
    clock.advance(10)

    assert run(store, "DBSIZE") == "(integer) 1"
    assert run(store, "GET token") == '"alive"'
    assert run(store, "TTL token") == "(integer) 10"


def test_expired_key_behaves_like_missing_key():
    """Expired keys are deleted before key-based commands respond."""
    clock = FakeClock()
    store = MiniRedis(clock=clock)

    assert run(store, "SET temp value") == "OK"
    assert run(store, "EXPIRE temp 1") == "(integer) 1"
    clock.advance(1)

    assert run(store, "GET temp") == "(nil)"
    assert run(store, "TTL temp") == "(integer) -2"
    assert run(store, "DEL temp") == "(integer) 0"
    assert run(store, "DBSIZE") == "(integer) 0"


def test_expire_missing_and_immediate_expire():
    """EXPIRE returns 0 for missing keys and deletes for non-positive seconds."""
    store = MiniRedis()

    assert run(store, "EXPIRE missing 5") == "(integer) 0"
    assert run(store, "SET temp value") == "OK"
    assert run(store, "EXPIRE temp 0") == "(integer) 1"
    assert run(store, "GET temp") == "(nil)"


def test_error_handling():
    """Wrong arity, unknown commands, and integer parsing use standard errors."""
    store = MiniRedis()

    assert run(store, "GET") == "(error) ERR wrong number of arguments for 'GET' command"
    assert run(store, "HELLO") == "(error) ERR unknown command 'HELLO'"
    assert run(store, "CONFIG SET maxmemory abc") == "(error) ERR value is not an integer or out of range"
    assert run(store, "CONFIG SET maxmemory -1") == "(error) ERR value is not an integer or out of range"
    assert run(store, "EXPIRE key abc") == "(error) ERR value is not an integer or out of range"
