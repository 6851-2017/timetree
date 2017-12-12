class SplayPredecessorDict:
    __slots__ = ('root',)

    class _Node:
        __slots__ = ('key', 'value', 'ch', 'par',)

        def __init__(self, key, value):
            self.key = key
            self.value = value
            self.par = None
            self.ch = [None, None]

        def d(self):
            return self.par.ch.index(self)

        def rot(self):
            p = self.par
            assert p is not None

            x = self.d()
            c = self.ch[1-x]

            g = p.par
            assert g is not None

            g.ch[p.d()] = self
            self.par = g

            self.ch[1-x] = p
            p.par = self

            p.ch[x] = c
            if c is not None:
                c.par = p

        def splay(self, root):
            assert root is not None
            while self.par is not root:
                if self.par.par is not root:
                    if self.d() == self.par.d():
                        # Zig-zig
                        self.par.rot()
                    else:
                        # Zig-zag
                        self.rot()
                self.rot()

    def __init__(self):
        self.root = self._Node(None, None)

    def get_pred(self, key):
        cur = self.root.ch[1]
        pred = None
        while cur is not None:
            if cur.key == key:
                cur.splay(self.root)
                return cur.value
            elif cur.key < key:
                pred = cur
                cur = cur.ch[1]
            else:
                cur = cur.ch[0]
        if pred is None:
            raise KeyError('No such element')
        pred.splay(self.root)
        return pred.value

    def set(self, key, value):
        par = self.root
        d = 1
        while par.ch[d] is not None:
            par = par.ch[d]
            if par.key == key:
                par.value = value
                par.splay(self.root)
                return
            elif par.key < key:
                d = 1
            else:
                d = 0

        node = self._Node(key, value)
        node.par = par
        par.ch[d] = node
        node.splay(self.root)
