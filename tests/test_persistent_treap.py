import random

import pytest

import timetree


@timetree.make_persistent
class Treap:
    @timetree.make_persistent
    class TreapNode:
        def __init__(self, value, key_val, priority, parent, child, is_right):
            self.value = value
            self.key_val = key_val
            self.priority = priority

            assert parent.right == child if is_right else parent.left == child
            assert child is None or child.parent == parent
            self.parent = parent
            if is_right:
                self.left = None
                self.right = child
                if parent is not None:
                    parent.right = self
            else:
                self.left = child
                self.right = None
                if parent is not None:
                    parent.left = self
            if child is not None:
                child.parent = self

        def __repr__(self):
            return 'TreapNode<%s,%s>' % (self.value, self.priority)

    def __init__(self, iterable=(), *, key=None):
        if key is None:
            key = (lambda x: x)
        self._key = key
        self.left = None
        self.right = None
        self.size = 0

        self.priority = 'root'
        self.value = 'root'

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
        Any given hint must make the correct binary search chioces (unchecked).
        """
        key_val = self.key(value)
        priority = random.random()

        if not isinstance(hint, self.TreapNode):
            hint = self
        # We'll use hint as our starting point
        parent = hint

        # go down to satisfy binary search tree invariant
        child = parent
        while child is not None:
            parent = child
            child = parent.right if parent is self or parent.key_val <= key_val else parent.left

        # add the value
        self.size += 1
        is_right = parent is self or parent.key_val <= key_val
        result = self.TreapNode(value, key_val, priority, parent, child, is_right)

        # go up to satisfy priority invariant
        while result.parent is not self and result.parent.priority <= priority:
            parent = result.parent
            # perform a rotation
            if parent.parent.left is parent:
                parent.parent.left = result
            else:
                assert parent.parent.right is parent
                parent.parent.right = result
            result.parent = parent.parent
            if parent.left is result:
                parent.left = result.right
                if result.right is not None:
                    result.right.parent = parent
                result.right = parent
            else:
                assert parent.right is result
                parent.right = result.left
                if result.left is not None:
                    result.left.parent = parent
                result.left = parent
            parent.parent = result
        return result

    def __len__(self):
        return self.size

    @timetree.make_persistent
    class _Iterator:
        def __init__(self, tree, reversed=False):
            self.tree = tree
            self.cur_node = tree
            self.reversed = reversed

        def __iter__(self):
            return self

        def __next__(self):
            result = self.cur_node
            if result.right is None:
                while result is not self.tree and \
                        result.parent.right is result:
                    result = result.parent
                if result is self.tree:
                    raise StopIteration
                result = result.parent
            else:
                result = result.right
                while result.left is not None:
                    result = result.left
            self.cur_node = result
            return result.value

    def __iter__(self):
        return self._Iterator(self)

    def __reversed__(self):
        return self._Iterator(self, reversed=True)

    def _repr(self, node):
        if node is None:
            return ''
        assert node.left is None or node.left.parent is node
        assert node.right is None or node.right.parent is node
        return '( %s %s %s )' % (self._repr(node.left), node.value, self._repr(node.right))

    def __repr__(self):
        return self._repr(self.right)


@pytest.mark.persistence_partial
def test_sorted_treap_commit(backend):
    lst = Treap(timetree_backend=backend)
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
def test_sorted_treap_branch(backend):
    lst = Treap(timetree_backend=backend)
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
