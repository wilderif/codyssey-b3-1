"""In-memory Redis-like string store with LRU and TTL support."""

import time

from mini_redis.data_structures.doubly_linked_list import DoublyLinkedList
from mini_redis.data_structures.hash_map import HashMap
from mini_redis.data_structures.min_heap import MinHeap


# Redis-style responses shared by multiple commands.
ERROR_INTEGER = "(error) ERR value is not an integer or out of range"
ERROR_OOM = "(error) OOM command not allowed when used_memory > 'maxmemory'"
OK = "OK"
NIL = "(nil)"
EMPTY_ARRAY = "(empty array)"

# Redis integer arguments use the signed 64-bit range.
MIN_INTEGER = -(1 << 63)
MAX_INTEGER = (1 << 63) - 1


def redis_integer(value):
    """Format an integer result in Redis style."""
    return f"(integer) {value}"


def redis_string(value):
    """Format a stored string value in Redis style."""
    return '"' + value + '"'


class RedisEntry:
    """All state associated with one stored key."""

    def __init__(self, key, value):
        """Create an entry without LRU or TTL state."""
        self.key = key
        self.value = value
        self.lru_node = None
        self.expire_at = None

    @property
    def memory(self):
        """Return memory usage according to the assignment formula."""
        return len(self.key.encode("utf-8")) + len(self.value.encode("utf-8"))


class MiniRedis:
    """Execute Mini Redis commands against custom data structures."""

    def __init__(self, clock=None):
        """Initialize the empty database and memory settings."""
        self._entries = HashMap()
        self._lru = DoublyLinkedList()
        self._expire_heap = MinHeap()
        self._clock = clock or time.time
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def set(self, key, value):
        """Set a string value, reset TTL, and evict by LRU when needed."""
        entry = self._live_entry(key)
        new_entry = RedisEntry(key, value)
        if self.maxmemory > 0 and new_entry.memory > self.maxmemory:
            return ERROR_OOM

        if entry is None:
            entry = new_entry
            self._entries.put(key, entry)
            entry.lru_node = self._lru.insert_front(key)
        else:
            # Account for the old value before replacing it with the new one.
            self.used_memory -= entry.memory
            entry.value = value
            entry.expire_at = None
            self._lru.move_to_front(entry.lru_node)

        self.used_memory += entry.memory
        self._evict_until_within_limit()
        return OK

    def get(self, key):
        """Return the value for a key and update LRU only on a hit."""
        entry = self._live_entry(key)
        if entry is None:
            return NIL
        self._lru.move_to_front(entry.lru_node)
        return redis_string(entry.value)

    def delete(self, key):
        """Delete a key from data, TTL, and LRU structures."""
        entry = self._live_entry(key)
        if entry is None:
            return redis_integer(0)
        self._delete_entry(entry)
        return redis_integer(1)

    def exists(self, key):
        """Return whether a key currently exists."""
        entry = self._live_entry(key)
        if entry is None:
            return redis_integer(0)
        return redis_integer(1)

    def dbsize(self):
        """Return the current number of unexpired keys."""
        self._purge_expired()
        return redis_integer(self._entries.size())

    def keys(self):
        """Return all keys as a Redis-style array-like listing."""
        self._purge_expired()
        keys = self._entries.keys()
        if len(keys) == 0:
            return EMPTY_ARRAY
        lines = []
        for index, key in enumerate(keys, start=1):
            lines.append(f"{index}. {redis_string(key)}")
        return "\n".join(lines)

    def config_set_maxmemory(self, value_text):
        """Set maxmemory after validating a non-negative integer."""
        value = self._parse_int(value_text)
        if value is None or value < 0:
            return ERROR_INTEGER
        self.maxmemory = value
        self._evict_until_within_limit()
        return OK

    def info_memory(self):
        """Return memory usage, limit, and eviction counter."""
        self._purge_expired()
        return "\n".join(
            [
                f"used_memory:{self.used_memory}",
                f"maxmemory:{self.maxmemory}",
                f"evicted_keys:{self.evicted_keys}",
            ]
        )

    def expire(self, key, seconds_text):
        """Set a key expiration in seconds."""
        seconds = self._parse_int(seconds_text)
        if seconds is None:
            return ERROR_INTEGER
        entry = self._live_entry(key)
        if entry is None:
            return redis_integer(0)
        if seconds <= 0:
            self._delete_entry(entry)
            return redis_integer(1)
        entry.expire_at = self._clock() + seconds
        self._expire_heap.push((entry.expire_at, key))
        return redis_integer(1)

    def ttl(self, key):
        """Return Redis-style TTL status for a key."""
        entry = self._live_entry(key)
        if entry is None:
            return redis_integer(-2)
        if entry.expire_at is None:
            return redis_integer(-1)
        remaining = entry.expire_at - self._clock()
        if remaining <= 0:
            self._delete_entry(entry)
            return redis_integer(-2)
        return redis_integer(int(remaining))

    def _parse_int(self, value_text):
        """Parse a signed 64-bit decimal integer."""
        if value_text is None or value_text == "":
            return None
        try:
            value = int(value_text)
        except (TypeError, ValueError):
            return None
        if value < MIN_INTEGER or value > MAX_INTEGER:
            return None
        return value

    def _live_entry(self, key):
        """Return an entry only if it exists and has not expired."""
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expire_at is None:
            return entry
        if entry.expire_at > self._clock():
            return entry
        self._delete_entry(entry)
        return None

    def _purge_expired(self):
        """Remove all currently expired keys from the TTL heap front."""
        now = self._clock()
        item = self._expire_heap.peek()
        while item is not None and item[0] <= now:
            expire_at, key = self._expire_heap.pop()
            entry = self._entries.get(key)
            # A different timestamp means this is an older, stale heap record.
            if entry is not None and entry.expire_at == expire_at:
                self._delete_entry(entry)
            item = self._expire_heap.peek()

    def _delete_entry(self, entry):
        """Remove an entry from the hash map, LRU, and memory total."""
        self._entries.remove(entry.key)
        self._lru.remove_node(entry.lru_node)
        self.used_memory -= entry.memory

    def _evict_until_within_limit(self):
        """Evict least recently used keys until memory is under maxmemory."""
        self._purge_expired()
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            # The linked-list tail is the least recently used key.
            key = self._lru.tail.data
            self._delete_entry(self._entries.get(key))
            self.evicted_keys += 1
