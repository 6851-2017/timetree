import weakref

from .bsearch_partial import BsearchPartialBackend
from .bsearch_partial import BsearchPartialDnode
from .bsearch_partial import BsearchPartialVnode

from .base_partial import BasePartialVersion


class SplitPartialBackend(BsearchPartialBackend):
    __slots__ = ()


class SplitPartialDnode(BsearchPartialDnode):
    __slots__ = ('_field_backrefs', '_vnode_backrefs', '__weakref__', '_in_split')

    def __init__(self):
        super().__init__()
        self._field_backrefs = weakref.WeakKeyDictionary()  # This should be a weak key default dict
        self._vnode_backrefs = weakref.WeakSet()
        self._in_split = False

    def set(self, field, value, version_num):
        if len(self.mods_dict[field]) > 0:
            # delete old backref
            old_value = self.get(field, version_num)
            if isinstance(old_value, SplitPartialDnode):
                if version_num > 62:
                    pass
                    print(old_value, dict(old_value._field_backrefs))
                old_value._field_backrefs[self].remove(field)

        super().set(field, value, version_num)

        # add new backref
        if isinstance(value, SplitPartialDnode):
            value._field_backrefs[self] = value._field_backrefs.get(self, set())
            value._field_backrefs[self].add(field)

        # split if necessary
        if len(self.mods_dict[field]) > 64:  # TODO: better split condition
            # print('split', self, field, self.mods_dict['val'][-1])
            new_dnode = SplitPartialDnode()

            # The order of these 3 loops is extremely important. I think I got it right this time, but I'm not 100% sure.

            for field, mod in [(field, mods[-1]) for field, mods in self.mods_dict.items()]:
                # copy fields
                new_dnode.mods_dict[field] = [mod]

                # update backreferences to this node
                value = mod.value
                if isinstance(value, SplitPartialDnode):
                    value._field_backrefs[self].remove(field)
                    value._field_backrefs[new_dnode] = value._field_backrefs.get(new_dnode, set())
                    value._field_backrefs[new_dnode].add(field)

            # update head vnodes
            for vnode in set(self._vnode_backrefs):
                if vnode.version.is_head:
                    assert vnode.version.version_num == version_num
                    self._vnode_backrefs.remove(vnode)
                    vnode.dnode = new_dnode
                    new_dnode._vnode_backrefs.add(vnode)

            # update forward references to this node, possibly causing chain reactions
            self._in_split = False
            new_dnode._in_split = True
            for vnode in [SplitPartialVnode(InternalPartialHead(version_num), dnode=dnode) for dnode in self._field_backrefs]:
                for field in set(self._field_backrefs[vnode.dnode]):
                    try:
                        vnode.dnode.set(field, new_dnode, version_num)
                    except:
                        print(vnode.dnode, field, new_dnode, version_num)
                        raise
                    if not new_dnode._in_split:
                        return
            new_dnode._in_split = False

    # def __repr__(self):
        # return 'SplitPartialDnode<%s, (%s, %s)>' % (self.mods_dict['val'][-1].value, self.mods_dict['val'][0].version, self.mods_dict['val'][-1].version)


class InternalPartialHead(BasePartialVersion):
    __slots__ = ('version_num', )

    def __init__(self, version_num):
        super().__init__(None, is_head=True)
        self.version_num = version_num

    def new_node(self):
        raise NotImplementedError('New node cannot be constructed from an internal version.')


class SplitPartialVnode(BsearchPartialVnode):
    __slots__ = ('__weakref__',)

    def __init__(self, version, *, dnode=None):
        dnode = dnode or SplitPartialDnode()
        super().__init__(version, dnode=dnode)

        self.dnode._vnode_backrefs.add(self)

    def __repr__(self):
        return 'SplitPartialVnode<%s, %s>' % (self.version.version_num, self.dnode)


SplitPartialBackend.vnode_cls = SplitPartialVnode
