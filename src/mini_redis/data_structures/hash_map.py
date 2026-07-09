"""Hash map with separate chaining and automatic resizing."""

from mini_redis.data_structures.doubly_linked_list import DoublyLinkedList


INITIAL_CAPACITY = 8
LOAD_FACTOR_LIMIT = 0.75


class HashEntry:
    """Key-value pair stored inside a hash bucket chain."""

    def __init__(self, key, value):
        """Store the key and value for one map entry."""
        self.key = key
        self.value = value


class HashMap:
    """Custom hash map using polynomial hashing and chaining."""

    def __init__(self):
        """Initialize buckets and entry count."""
        self._capacity = INITIAL_CAPACITY
        self._buckets = self._make_buckets(self._capacity)
        self._size = 0

    def _make_buckets(self, capacity):
        """Create a fixed-size bucket array."""
        buckets = []
        index = 0
        while index < capacity:
            buckets.append(DoublyLinkedList())
            index += 1
        return buckets

    def _hash(self, key):
        """Return a deterministic polynomial rolling hash for a string key."""
        text = str(key)
        value = 0
        index = 0
        while index < len(text):
            value = (value * 131 + ord(text[index])) & 0xFFFFFFFFFFFFFFFF
            index += 1
        return value

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

    def _resize_if_needed(self):
        """Double bucket capacity after the load factor exceeds the limit."""
        if self._size / self._capacity <= LOAD_FACTOR_LIMIT:
            return
        old_buckets = self._buckets
        self._capacity *= 2
        self._buckets = self._make_buckets(self._capacity)
        old_size = self._size
        self._size = 0
        bucket_index = 0
        while bucket_index < len(old_buckets):
            current = old_buckets[bucket_index].head
            while current is not None:
                self.put(current.data.key, current.data.value)
                current = current.next
            bucket_index += 1
        self._size = old_size

    def put(self, key, value):
        """Insert or update a key-value pair."""
        node = self._find_node(key)
        if node is not None:
            node.data.value = value
            return False
        bucket = self._buckets[self._bucket_index(key)]
        bucket.insert_back(HashEntry(key, value))
        self._size += 1
        self._resize_if_needed()
        return True

    def get(self, key):
        """Return the value for key, or None if missing."""
        node = self._find_node(key)
        if node is None:
            return None
        return node.data.value

    def remove(self, key):
        """Remove key and return its value, or None if missing."""
        bucket = self._buckets[self._bucket_index(key)]
        current = bucket.head
        while current is not None:
            if current.data.key == key:
                value = current.data.value
                bucket.remove_node(current)
                self._size -= 1
                return value
            current = current.next
        return None

    def contains(self, key):
        """Return True when key exists in the map."""
        return self._find_node(key) is not None

    def keys(self):
        """Return a list of all stored keys."""
        result = []
        bucket_index = 0
        while bucket_index < len(self._buckets):
            current = self._buckets[bucket_index].head
            while current is not None:
                result.append(current.data.key)
                current = current.next
            bucket_index += 1
        return result

    def size(self):
        """Return the number of entries in the map."""
        return self._size

