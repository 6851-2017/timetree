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
