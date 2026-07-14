"""Doubly linked list implementation for O(1) node updates."""


class DoublyLinkedNode:
    """Node storing payload data and links to adjacent nodes."""

    def __init__(self, data):
        """Create a node with previous and next links."""
        self.prev = None
        self.next = None
        self.data = data


class DoublyLinkedList:
    """Doubly linked list with direct node removal and movement."""

    def __init__(self):
        """Initialize an empty list."""
        self.head = None
        self.tail = None
        self._size = 0

    def size(self):
        """Return the number of nodes in the list."""
        return self._size

    def insert_front(self, data):
        """Insert data at the front and return the new node."""
        node = DoublyLinkedNode(data)
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1
        return node

    def insert_back(self, data):
        """Insert data at the back and return the new node."""
        node = DoublyLinkedNode(data)
        node.prev = self.tail
        if self.tail is not None:
            self.tail.next = node
        self.tail = node
        if self.head is None:
            self.head = node
        self._size += 1
        return node

    def remove_front(self):
        """Remove the front node and return its data, or None."""
        if self.head is None:
            return None
        return self.remove_node(self.head)

    def remove_back(self):
        """Remove the back node and return its data, or None."""
        if self.tail is None:
            return None
        return self.remove_node(self.tail)

    def remove_node(self, node):
        """Remove an existing node in O(1) and return its data."""
        if node is None:
            return None
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = None
        node.next = None
        self._size -= 1
        return node.data

    def move_to_front(self, node):
        """Move an existing node to the front in O(1)."""
        if node is None or node is self.head:
            return
        if node.prev is not None:
            node.prev.next = node.next
        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev
        node.prev = None
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node

    def iter_data(self):
        """Yield node data from front to back."""
        current = self.head
        while current is not None:
            yield current.data
            current = current.next
