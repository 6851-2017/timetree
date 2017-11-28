import pytest

import timetree


@timetree.make_persistent
class A(object):
    pass


def test_main():
    dir(timetree)


def test_frontend():
    a = A(timetree_backend=timetree.backend.NopBackend())
    a.foo = 1
    assert a.foo == 1
    assert timetree.frontend.get_vnode(a).get('foo') == 1
    timetree.frontend.get_vnode(a).set('bar', 2)
    assert a.bar == 2


def test_nop_backend():
    backend = timetree.backend.NopBackend()
    head, _ = backend.branch([])
    vnode = head.new_node()
    vnode.set('f', 5)
    assert vnode.get('f') == 5


def test_copy_backend():
    backend = timetree.backend.CopyBackend()
    head, _ = backend.branch([])
    vnode = head.new_node()
    vnode.set('f', 5)
    assert vnode.get('f') == 5
    # test commit
    commit, [old_vnode] = backend.commit([vnode])
    vnode.set('f', 8)
    assert vnode.get('f') == 8
    assert old_vnode.get('f') == 5
    # test full
    head2, [vnode2] = backend.branch([old_vnode])
    vnode2.set('f', 9)
    assert vnode.get('f') == 8
    assert old_vnode.get('f') == 5
    assert vnode2.get('f') == 9
    # test confluence
    commit2, [vnode3] = backend.commit([vnode])
    head, [new_vnode, new_vnode3] = backend.branch([old_vnode, vnode3])
    assert new_vnode.get('f') == 5
    assert new_vnode3.get('f') == 8


@pytest.mark.skip
def test_copy_no_commit():
    with timetree.use_backend(timetree.backend.copy.CopyBackend):
        timetree.branch()
        a = A()
        a.num = 3
        assert a.num == 3


@pytest.mark.skip
def test_copy_commit():
    with timetree.use_backend(timetree.backend.copy.CopyBackend):
        timetree.branch()
        a = A()
        a.num = 3
        assert a.num == 3
        b = timetree.commit(a)
        assert a.num == 3
        assert b.num == 3
