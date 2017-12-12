import pytest

import timetree


@timetree.make_persistent
class SortedLinkedList:
    @timetree.make_persistent
    class LinkedNode:
        def __init__(self, value, key_val, prev, next):
            self.value = value
            self.key_val = key_val

            assert prev.next == next
            assert next.prev == prev
            self.prev = prev
            self.prev.next = self
            self.next = next
            self.next.prev = self

    def __init__(self, iterable=(), *, key=None):
        if key is None:
            key = (lambda x: x)
        self._key = key
        self.next = self
        self.prev = self
        self.size = 0

        cur_hint = None
        for v in iterable:
            cur_hint = self.add(v, hint=cur_hint)

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, 'key function')

    def add(self, value, hint=None):
        """ Insert value into this set, after all existing copies
        """
        key_val = self.key(value)

        if isinstance(hint, self.LinkedNode):
            # We'll use hint as our starting point instead
            before_point = hint
            after_point = hint.next
        else:
            # Insert new_node after the insertion point
            before_point = self.prev
            after_point = self

        while before_point is not self and before_point.key_val > key_val:
            before_point = before_point.prev
            after_point = after_point.prev

        while after_point is not self and after_point.key_val <= key_val:
            before_point = before_point.next
            after_point = after_point.next

        self.size += 1

        return self.LinkedNode(value, key_val, before_point, after_point)

    def __len__(self):
        return self.size

    @timetree.make_persistent
    class _Iterator:
        def __init__(self, list, reversed=False):
            self.list = list
            self.cur_node = list
            self.reversed = reversed

        def __iter__(self):
            return self

        def __next__(self):
            result = self.cur_node.prev if self.reversed else self.cur_node.next
            if result is self.list:
                raise StopIteration
            self.cur_node = result
            return result.value

    def __iter__(self):
        return self._Iterator(self)

    def __reversed__(self):
        return self._Iterator(self, reversed=True)


@pytest.mark.persistence_partial
def test_sorted_linked_list_commit(backend):
    lst = SortedLinkedList(timetree_backend=backend)
    lst.add(1)
    lst.add(7)
    lst.add(3)
    assert list(lst) == [1, 3, 7]
    old_lst = timetree.commit(lst)
    assert list(old_lst) == [1, 3, 7]
    lst.add(12)
    lst.add(4)
    lst.add(2)
    lst.add(5)
    assert list(lst) == [1, 2, 3, 4, 5, 7, 12]
    assert list(old_lst) == [1, 3, 7]


@pytest.mark.persistence_full
def test_sorted_linked_list_branch(backend):
    lst = SortedLinkedList(timetree_backend=backend)
    lst.add(1)
    lst.add(7)
    lst.add(3)
    assert list(lst) == [1, 3, 7]
    old_lst = timetree.commit(lst)
    assert list(old_lst) == [1, 3, 7]
    lst.add(12)
    lst.add(4)
    lst.add(2)
    lst.add(5)
    assert list(lst) == [1, 2, 3, 4, 5, 7, 12]
    assert list(old_lst) == [1, 3, 7]

    new_lst = timetree.branch(old_lst)
    assert list(lst) == [1, 2, 3, 4, 5, 7, 12]
    assert list(old_lst) == [1, 3, 7]
    assert list(new_lst) == [1, 3, 7]
    new_lst.add(4)
    lst.add(6)
    new_lst.add(20)
    assert list(lst) == [1, 2, 3, 4, 5, 6, 7, 12]
    assert list(old_lst) == [1, 3, 7]
    assert list(new_lst) == [1, 3, 4, 7, 20]
