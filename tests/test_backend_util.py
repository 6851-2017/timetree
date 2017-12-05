import random

import pytest

from timetree.backend.util.order_maintenance import ExponentialLabelerListMixin
from timetree.backend.util.order_maintenance import ExponentialLabelerNodeMixin
from timetree.backend.util.order_maintenance import FastLabelerListMixin
from timetree.backend.util.order_maintenance import FastLabelerNodeMixin
from timetree.backend.util.order_maintenance import QuadraticLabelerListMixin
from timetree.backend.util.order_maintenance import QuadraticLabelerNodeMixin


@pytest.mark.parametrize("lst_fn,node_fn", [
    pytest.param(
        lambda: ExponentialLabelerListMixin(capacity=2),
        lambda: ExponentialLabelerNodeMixin(),
        marks=pytest.mark.xfail(raises=ExponentialLabelerNodeMixin.LabelError),
    ),
    pytest.param(
        lambda: QuadraticLabelerListMixin(),
        lambda: QuadraticLabelerNodeMixin(),
    ),
    pytest.param(
        lambda: FastLabelerListMixin(),
        lambda: FastLabelerNodeMixin(),
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

        new_node.insert(insert_point)

        assert insert_point.next == new_node and new_node.prev == insert_point

        labels = [node.label for node in lst]
        assert all(l1 < l2 for l1, l2 in zip(labels, labels[1:]))
