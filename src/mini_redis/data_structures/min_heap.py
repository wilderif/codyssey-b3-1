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
        if not self._items:
            return None
        root = self._items[0]
        last = self._items.pop()
        if self._items:
            self._items[0] = last
            self._heapify_down(0)
        return root

    def peek(self):
        """Return the smallest item without removing it."""
        if not self._items:
            return None
        return self._items[0]

    def _heapify_up(self, index):
        """Move an item upward until parent order is valid."""
        while index > 0:
            parent_index = (index - 1) // 2
            if not self._items[index] < self._items[parent_index]:
                break
            self._swap(index, parent_index)
            index = parent_index

    def _heapify_down(self, index):
        """Move an item downward until child order is valid."""
        item_count = len(self._items)
        while True:
            left_index = index * 2 + 1
            right_index = index * 2 + 2
            smallest_index = index
            if (
                left_index < item_count
                and self._items[left_index] < self._items[smallest_index]
            ):
                smallest_index = left_index
            if (
                right_index < item_count
                and self._items[right_index] < self._items[smallest_index]
            ):
                smallest_index = right_index
            if smallest_index == index:
                break
            self._swap(index, smallest_index)
            index = smallest_index

    def _swap(self, left, right):
        """Swap two heap positions."""
        self._items[left], self._items[right] = self._items[right], self._items[left]
