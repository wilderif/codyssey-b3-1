"""Array-backed minimum heap for TTL expiration ordering."""


class MinHeap:
    """Binary min heap storing values that support less-than comparison."""

    def __init__(self):
        """Initialize an empty heap array."""
        self._items = []

    def size(self):
        """Return the number of heap items."""
        return len(self._items)

    def push(self, item):
        """Insert an item and restore heap order."""
        self._items.append(item)
        self._heapify_up(len(self._items) - 1)

    def pop(self):
        """Remove and return the smallest item, or None when empty."""
        if len(self._items) == 0:
            return None
        root = self._items[0]
        last = self._items.pop()
        if len(self._items) > 0:
            self._items[0] = last
            self._heapify_down(0)
        return root

    def peek(self):
        """Return the smallest item without removing it."""
        if len(self._items) == 0:
            return None
        return self._items[0]

    def _heapify_up(self, index):
        """Move an item upward until parent order is valid."""
        while index > 0:
            parent = (index - 1) // 2
            if not self._items[index] < self._items[parent]:
                break
            self._swap(index, parent)
            index = parent

    def _heapify_down(self, index):
        """Move an item downward until child order is valid."""
        size = len(self._items)
        while True:
            left = index * 2 + 1
            right = index * 2 + 2
            smallest = index
            if left < size and self._items[left] < self._items[smallest]:
                smallest = left
            if right < size and self._items[right] < self._items[smallest]:
                smallest = right
            if smallest == index:
                break
            self._swap(index, smallest)
            index = smallest

    def _swap(self, left, right):
        """Swap two heap positions."""
        self._items[left], self._items[right] = self._items[right], self._items[left]

