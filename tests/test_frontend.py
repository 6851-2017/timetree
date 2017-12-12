import pytest

import timetree


@timetree.make_persistent
class PersistentObject(object):
    pass


@pytest.mark.persistence_none
def test_frontend_wrapper(backend):
    with timetree.use_backend(backend):
        a = PersistentObject()
        a.b = PersistentObject()
    a.foo = 1
    a.b.foo = 2
    assert a.foo == 1
    assert a.b.foo == 2
    assert timetree.frontend._vnode_to_proxy(a).get('foo') == 1
    assert timetree.frontend._vnode_to_proxy(a.b).get('foo') == 2
    timetree.frontend._vnode_to_proxy(a).set('bar', 2)
    timetree.frontend._vnode_to_proxy(a.b).set('bar', 3)
    assert a.bar == 2
    assert a.b.bar == 3


@pytest.mark.persistence_partial
def test_frontend_commit(backend):
    with timetree.use_backend(backend):
        a = PersistentObject()
        a.b = PersistentObject()
    a.num = 3
    a.b.val = 'hello!'
    old_a = timetree.commit(a)
    a.num = 4
    a.b.val = 'world!'
    assert a.num == 4
    assert a.b.val == 'world!'
    assert old_a.num == 3
    assert old_a.b.val == 'hello!'


@pytest.mark.persistence_full
def test_frontend_branch(backend):
    a = PersistentObject(timetree_backend=backend)
    a.num = 3
    b = timetree.branch(a)
    b.num = 5
    assert a.num == 3
    assert b.num == 5
    a.num = 4
    assert a.num == 4
    assert b.num == 5
