import pytest

import timetree


@timetree.make_persistent
class A(object):
    pass


def test_main():
    dir(timetree)


@pytest.mark.persistence_none
def test_frontend(backend):
    a = A(timetree_backend=backend)
    a.foo = 1
    assert a.foo == 1
    assert timetree.frontend.get_vnode(a).get('foo') == 1
    timetree.frontend.get_vnode(a).set('bar', 2)
    assert a.bar == 2


@pytest.mark.persistence_partial
def test_frontend_commit(backend):
    a = A(timetree_backend=backend)
    a.num = 3
    b = timetree.commit(a)
    a.num = 4
    assert b.num == 3
    assert a.num == 4


@pytest.mark.persistence_full
def test_frontend_branch(backend):
    a = A(timetree_backend=backend)
    a.num = 3
    b = timetree.branch(a)
    b.num = 5
    assert a.num == 3
    assert b.num == 5
    a.num = 4
    assert a.num == 4
    assert b.num == 5
