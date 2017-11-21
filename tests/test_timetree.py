import timetree

class A(object, metaclass=timetree.Persistent):
    pass

def test_main():
    dir(timetree)

def test_dumb():
    with timetree.use_backend(timetree.backend.copy.CopyBackend):
        timetree.branch()
        a = A()
        a.num = 3
        assert a.num == 3
        b = timetree.commit(a)
        assert a.num == 3
        assert b.num == 3
