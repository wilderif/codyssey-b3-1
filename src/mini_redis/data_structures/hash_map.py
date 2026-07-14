"""Hash map with separate chaining and automatic resizing."""

from mini_redis.data_structures.doubly_linked_list import DoublyLinkedList


# The bucket array doubles only after the load factor exceeds 0.75.
INITIAL_CAPACITY = 8
LOAD_FACTOR_LIMIT = 0.75

# FNV-1a 64-bit constants keep the custom hash deterministic.
FNV_OFFSET_BASIS = 14695981039346656037
FNV_PRIME = 1099511628211
MASK_64 = 0xFFFFFFFFFFFFFFFF


class HashEntry:
    """Key-value pair stored inside a hash bucket chain."""

    def __init__(self, key, value):
        """Store the key and value for one map entry."""
        self.key = key
        self.value = value


class HashMap:
    """Custom hash map using FNV-1a 64-bit hashing and chaining."""

    def __init__(self):
        """Initialize buckets and entry count."""
        self._capacity = INITIAL_CAPACITY
        self._buckets = self._make_buckets(self._capacity)
        self._size = 0

    def _make_buckets(self, capacity):
        """Create a fixed-size bucket array."""
        return [DoublyLinkedList() for _ in range(capacity)]

    def _hash(self, key):
        """Return a deterministic FNV-1a 64-bit hash for a string key."""
        hash_value = FNV_OFFSET_BASIS
        for byte in str(key).encode("utf-8"):
            hash_value = hash_value ^ byte
            hash_value = (hash_value * FNV_PRIME) & MASK_64
        return hash_value

    def _bucket_index(self, key):
        """Return the bucket index for a key."""
        return self._hash(key) % self._capacity

    def _find_node(self, key):
        """Find the node containing key inside its bucket chain."""
        bucket = self._buckets[self._bucket_index(key)]
        current = bucket.head
        while current is not None:
            if current.data.key == key:
                return current
            current = current.next
        return None

    def _resize(self):
        """Double the capacity and move entries into their new buckets."""
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = self._make_buckets(self._capacity)

        for bucket in old_buckets:
            for entry in bucket.iter_data():
                new_bucket = self._buckets[self._bucket_index(entry.key)]
                new_bucket.insert_back(entry)

    def put(self, key, value):
        """Insert or update a key-value pair."""
        node = self._find_node(key)
        if node is not None:
            node.data.value = value
            return False
        bucket = self._buckets[self._bucket_index(key)]
        bucket.insert_back(HashEntry(key, value))
        self._size += 1
        if self._size > self._capacity * LOAD_FACTOR_LIMIT:
            self._resize()
        return True

    def get(self, key):
        """Return the value for key, or None if missing."""
        node = self._find_node(key)
        if node is None:
            return None
        return node.data.value

    def remove(self, key):
        """Remove key and return its value, or None if missing."""
        node = self._find_node(key)
        if node is None:
            return None
        bucket = self._buckets[self._bucket_index(key)]
        entry = bucket.remove_node(node)
        self._size -= 1
        return entry.value

    def contains(self, key):
        """Return True when key exists in the map."""
        return self._find_node(key) is not None

    def keys(self):
        """Return a list of all stored keys."""
        result = []
        for bucket in self._buckets:
            for entry in bucket.iter_data():
                result.append(entry.key)
        return result

    def size(self):
        """Return the number of entries in the map."""
        return self._size
