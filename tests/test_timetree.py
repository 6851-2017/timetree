import timetree


class A(object, metaclass=timetree.Persistent):
    pass


def test_main():
    dir(timetree)


def test_nop_backend():
    backend = timetree.backend.NopBackend()
    head, _ = backend.branch([])
    vnode = head.new_node()
    vnode.set('f', 5)
    assert vnode.get('f') == 5


'''
def test_copy_no_commit():
    with timetree.use_backend(timetree.backend.copy.CopyBackend):
        timetree.branch()
        a = A()
        a.num = 3
        assert a.num == 3

def test_copy_commit():
    with timetree.use_backend(timetree.backend.copy.CopyBackend):
        timetree.branch()
        a = A()
        a.num = 3
        assert a.num == 3
        b = timetree.commit(a)
        assert a.num == 3
        assert b.num == 3
'''
