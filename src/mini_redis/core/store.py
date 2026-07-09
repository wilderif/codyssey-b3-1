"""In-memory Redis-like string store with LRU and TTL support."""

import time

from mini_redis.data_structures.doubly_linked_list import DoublyLinkedList
from mini_redis.data_structures.hash_map import HashMap
from mini_redis.data_structures.min_heap import MinHeap


ERROR_INTEGER = "(error) ERR value is not an integer or out of range"
ERROR_OOM = "(error) OOM command not allowed when used_memory > 'maxmemory'"


class RedisEntry:
    """Stored string value with its accounting metadata."""

    def __init__(self, key, value):
        """Store key, value, and computed memory footprint."""
        self.key = key
        self.value = value
        self.memory = len(key.encode("utf-8")) + len(value.encode("utf-8"))


class ExpireItem:
    """Heap item ordered by expiration time and insertion sequence."""

    def __init__(self, expire_at, sequence, key):
        """Create an expiration record for lazy TTL deletion."""
        self.expire_at = expire_at
        self.sequence = sequence
        self.key = key

    def __lt__(self, other):
        """Compare by expiration time, then sequence for stable ordering."""
        if self.expire_at == other.expire_at:
            return self.sequence < other.sequence
        return self.expire_at < other.expire_at


class MiniRedis:
    """Execute Mini Redis commands against custom data structures."""

    def __init__(self, clock=None):
        """Initialize the empty database and memory settings."""
        self._entries = HashMap()
        self._lru = DoublyLinkedList()
        self._lru_nodes = HashMap()
        self._expires = HashMap()
        self._expire_heap = MinHeap()
        self._clock = clock or time.time
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0
        self._expire_sequence = 0

    def set(self, key, value):
        """Set a string value, reset TTL, and evict by LRU when needed."""
        self._purge_expired()
        new_entry = RedisEntry(key, value)
        if self.maxmemory > 0 and new_entry.memory > self.maxmemory:
            return ERROR_OOM

        old_entry = self._entries.get(key)
        if old_entry is not None:
            self.used_memory -= old_entry.memory
        self._entries.put(key, new_entry)
        self.used_memory += new_entry.memory
        self._clear_expire(key)
        self._touch(key)

        if not self._evict_until_within_limit():
            return ERROR_OOM
        return "OK"

    def get(self, key):
        """Return the value for a key and update LRU only on a hit."""
        if self._is_expired(key):
            self._delete_key(key, count_eviction=False)
            return "(nil)"
        entry = self._entries.get(key)
        if entry is None:
            return "(nil)"
        self._touch(key)
        return '"' + entry.value + '"'

    def delete(self, key):
        """Delete a key from data, TTL, and LRU structures."""
        if self._is_expired(key):
            self._delete_key(key, count_eviction=False)
            return "(integer) 0"
        if self._delete_key(key, count_eviction=False):
            return "(integer) 1"
        return "(integer) 0"

    def exists(self, key):
        """Return whether a key currently exists."""
        if self._is_expired(key):
            self._delete_key(key, count_eviction=False)
            return "(integer) 0"
        if self._entries.contains(key):
            return "(integer) 1"
        return "(integer) 0"

    def dbsize(self):
        """Return the current number of unexpired keys."""
        self._purge_expired()
        return "(integer) " + str(self._entries.size())

    def keys(self):
        """Return all keys as a Redis-style array-like listing."""
        self._purge_expired()
        keys = self._entries.keys()
        if len(keys) == 0:
            return "(empty array)"
        lines = []
        index = 0
        while index < len(keys):
            lines.append(str(index + 1) + '. "' + keys[index] + '"')
            index += 1
        return "\n".join(lines)

    def config_set_maxmemory(self, value_text):
        """Set maxmemory after validating a non-negative integer."""
        value = self._parse_non_negative_int(value_text)
        if value is None:
            return ERROR_INTEGER
        self.maxmemory = value
        if not self._evict_until_within_limit():
            return ERROR_OOM
        return "OK"

    def info_memory(self):
        """Return memory usage, limit, and eviction counter."""
        self._purge_expired()
        return "\n".join(
            [
                "used_memory:" + str(self.used_memory),
                "maxmemory:" + str(self.maxmemory),
                "evicted_keys:" + str(self.evicted_keys),
            ]
        )

    def expire(self, key, seconds_text):
        """Set a key expiration in seconds."""
        seconds = self._parse_int(seconds_text)
        if seconds is None:
            return ERROR_INTEGER
        if self._is_expired(key):
            self._delete_key(key, count_eviction=False)
            return "(integer) 0"
        if not self._entries.contains(key):
            return "(integer) 0"
        if seconds <= 0:
            self._delete_key(key, count_eviction=False)
            return "(integer) 1"
        expire_at = self._clock() + seconds
        self._expires.put(key, expire_at)
        self._expire_sequence += 1
        self._expire_heap.push(ExpireItem(expire_at, self._expire_sequence, key))
        return "(integer) 1"

    def ttl(self, key):
        """Return Redis-style TTL status for a key."""
        if self._is_expired(key):
            self._delete_key(key, count_eviction=False)
            return "(integer) -2"
        if not self._entries.contains(key):
            return "(integer) -2"
        expire_at = self._expires.get(key)
        if expire_at is None:
            return "(integer) -1"
        remaining = expire_at - self._clock()
        if remaining <= 0:
            self._delete_key(key, count_eviction=False)
            return "(integer) -2"
        return "(integer) " + str(int(remaining))

    def _parse_int(self, value_text):
        """Parse a decimal integer without accepting floats or empty input."""
        if value_text is None or value_text == "":
            return None
        start = 0
        if value_text[0] == "-":
            if len(value_text) == 1:
                return None
            start = 1
        index = start
        while index < len(value_text):
            if value_text[index] < "0" or value_text[index] > "9":
                return None
            index += 1
        return int(value_text)

    def _parse_non_negative_int(self, value_text):
        """Parse an integer and reject negative values."""
        value = self._parse_int(value_text)
        if value is None or value < 0:
            return None
        return value

    def _touch(self, key):
        """Mark a key as most recently used."""
        node = self._lru_nodes.get(key)
        if node is None:
            node = self._lru.insert_front(key)
            self._lru_nodes.put(key, node)
            return
        self._lru.move_to_front(node)

    def _clear_expire(self, key):
        """Remove active TTL metadata for a key; stale heap items remain."""
        self._expires.remove(key)

    def _is_expired(self, key):
        """Return True when key has a TTL that is already elapsed."""
        expire_at = self._expires.get(key)
        return expire_at is not None and expire_at <= self._clock()

    def _purge_expired(self):
        """Remove all currently expired keys from the TTL heap front."""
        now = self._clock()
        item = self._expire_heap.peek()
        while item is not None and item.expire_at <= now:
            item = self._expire_heap.pop()
            active_expire_at = self._expires.get(item.key)
            if active_expire_at is not None and active_expire_at == item.expire_at:
                self._delete_key(item.key, count_eviction=False)
            item = self._expire_heap.peek()

    def _delete_key(self, key, count_eviction):
        """Delete key from every structure and optionally count eviction."""
        entry = self._entries.remove(key)
        if entry is None:
            self._expires.remove(key)
            return False
        self.used_memory -= entry.memory
        node = self._lru_nodes.remove(key)
        if node is not None:
            self._lru.remove_node(node)
        self._expires.remove(key)
        if count_eviction:
            self.evicted_keys += 1
        return True

    def _evict_until_within_limit(self):
        """Evict least recently used keys until memory is under maxmemory."""
        self._purge_expired()
        while self.maxmemory > 0 and self.used_memory > self.maxmemory:
            key = self._lru.remove_back()
            if key is None:
                return False
            self._lru_nodes.remove(key)
            entry = self._entries.remove(key)
            self._expires.remove(key)
            if entry is not None:
                self.used_memory -= entry.memory
                self.evicted_keys += 1
        return True

