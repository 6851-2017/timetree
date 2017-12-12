import random

import pytest

from timetree.backend.util.order_maintenance import ExponentialLabelerList
from timetree.backend.util.order_maintenance import ExponentialLabelerNode
from timetree.backend.util.order_maintenance import FastLabelerList
from timetree.backend.util.order_maintenance import FastLabelerNode
from timetree.backend.util.order_maintenance import QuadraticLabelerList
from timetree.backend.util.order_maintenance import QuadraticLabelerNode
from timetree.backend.util.predecessor import SplayPredecessorDict


@pytest.mark.parametrize("lst_fn,node_fn", [
    pytest.param(
        lambda: ExponentialLabelerList(capacity=2),
        lambda: ExponentialLabelerNode(),
        marks=pytest.mark.xfail(raises=ExponentialLabelerList.LabelError),
    ),
    pytest.param(
        lambda: QuadraticLabelerList(),
        lambda: QuadraticLabelerNode(),
    ),
    pytest.param(
        lambda: FastLabelerList(),
        lambda: FastLabelerNode(),
    ),
], ids=['ExponentialLabeler', 'QuadraticLabeler', 'FastLabeler'])
def test_labeler(lst_fn, node_fn):
    lst = lst_fn()

    def insert_random(): return random.choice([lst] + list(lst))

    def insert_front(): return lst

    def insert_back(): return lst.prev

    insert_ops = []
    insert_ops += [insert_back] * 100
    insert_ops += [insert_front] * 100
    insert_ops += [insert_random] * 100
    insert_ops += [insert_back] * 100
    insert_ops += [insert_front] * 100

    for insert_fn in insert_ops:
        # Grab a new node
        new_node = node_fn()

        # Insert based on the function
        insert_point = insert_fn()

        new_node.insert_self(insert_point)

        assert insert_point.next == new_node and new_node.prev == insert_point

        labels = [node.label for node in lst]
        assert all(l1 < l2 for l1, l2 in zip(labels, labels[1:]))


def test_predecessor():
    dct = SplayPredecessorDict()

    with pytest.raises(KeyError):
        dct.get_pred(-1)
    with pytest.raises(KeyError):
        dct.get_pred(20)

    dct.set(3, 'val 3')

    with pytest.raises(KeyError):
        dct.get_pred(-2)
    assert dct.get_pred(3) == 'val 3'
    assert dct.get_pred(5) == 'val 3'

    dct.set(3, 'other val 3')
    dct.set(5, 'val 5')
    dct.set(-1, 'val 2')

    assert dct.get_pred(3) == 'other val 3'
    assert dct.get_pred(4) == 'other val 3'
    assert dct.get_pred(5) == 'val 5'
    assert dct.get_pred(-1) == 'val 2'
    with pytest.raises(KeyError):
        dct.get_pred(-2)
