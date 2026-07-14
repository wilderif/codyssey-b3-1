"""Direct tests for the custom data structures required by the assignment."""

from mini_redis.data_structures.doubly_linked_list import DoublyLinkedList
from mini_redis.data_structures.hash_map import HashMap
from mini_redis.data_structures.min_heap import MinHeap


class CollisionHashMap(HashMap):
    """Hash map variant that places every key in the same bucket."""

    def _hash(self, key):
        """Force collisions so chaining behavior can be tested."""
        return 0


def test_doubly_linked_list_operations_keep_links_consistent():
    """All required insert, remove, and move operations preserve links."""
    linked = DoublyLinkedList()
    middle = linked.insert_front("middle")
    front = linked.insert_front("front")
    back = linked.insert_back("back")

    assert list(linked.iter_data()) == ["front", "middle", "back"]
    assert linked.size() == 3
    assert linked.head is front
    assert linked.tail is back
    assert middle.prev is front and middle.next is back

    linked.move_to_front(back)
    assert list(linked.iter_data()) == ["back", "front", "middle"]
    assert linked.head.prev is None
    assert linked.tail.next is None

    assert linked.remove_node(front) == "front"
    assert linked.remove_front() == "back"
    assert linked.remove_back() == "middle"
    assert linked.remove_front() is None
    assert linked.remove_back() is None
    assert linked.size() == 0


def test_hash_map_chaining_update_remove_and_resize():
    """Collisions chain correctly and resizing preserves every entry."""
    table = CollisionHashMap()

    for index in range(7):
        assert table.put("key:" + str(index), "value:" + str(index)) is True

    assert table._capacity == 16
    assert table.size() == 7
    assert table.put("key:3", "updated") is False
    assert table.get("key:3") == "updated"
    assert table.contains("key:6") is True
    assert sorted(table.keys()) == ["key:" + str(index) for index in range(7)]

    assert table.remove("key:3") == "updated"
    assert table.remove("missing") is None
    assert table.contains("key:3") is False
    assert table.size() == 6


def test_min_heap_returns_items_in_ascending_order():
    """Push, peek, pop, and both heapify directions maintain heap order."""
    heap = MinHeap()
    items = [(5, "e"), (1, "b"), (3, "d"), (1, "a"), (2, "c")]

    for item in items:
        heap.push(item)

    assert heap.size() == 5
    assert heap.peek() == (1, "a")
    assert [heap.pop() for _ in range(5)] == sorted(items)
    assert heap.peek() is None
    assert heap.pop() is None
    assert heap.size() == 0
