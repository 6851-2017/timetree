from collections import defaultdict
import weakref

from .bsearch_partial import BsearchPartialBackend
from .bsearch_partial import BsearchPartialDnode
from .bsearch_partial import BsearchPartialVnode

class SplitPartialBackend(BsearchPartialBackend):
    __slots__ = ()

class SplitPartialDnode(BsearchPartialDnode):
    __slots__ = ('_field_backrefs', '_vnode_backrefs', '__weakref__')

    def __init__(self):
        super().__init__()
        # TODO: Init the backend
        self._field_backrefs = weakref.WeakKeyDictionary()
        self._vnode_backrefs = weakref.WeakSet()

    def set(self, field, value, version_num):
        if len(self.mods_dict[field]) > 0:
            # delete old backref
            old_value = self.get(field, version_num)
            if isinstance(old_value, SplitPartialDnode):
                old_value._field_backrefs[self].remove(field)

        super().set(field, value, version_num)

        # add new backref
        if isinstance(value, SplitPartialDnode):
            value._field_backrefs[self] = value._field_backrefs.get(self, set())
            value._field_backrefs[self].add(field)

        # split if necessary
        if len(self.mods_dict[field]) > 64: #TODO: better split condition
            print('split', self)
            new_dnode = SplitPartialDnode()

            for field, mods in self.mods_dict.items():
                new_dnode.mods_dict[field] = [mods[-1]]

            for dnode, fields in self._field_backrefs.items():
                for field in set(fields):
                    dnode.set(field, new_dnode, version_num)

            for vnode in set(self._vnode_backrefs):
                if vnode.version.is_head:
                    assert vnode.version.version_num == version_num
                    self._vnode_backrefs.remove(vnode)
                    vnode.dnode = new_dnode
                    new_dnode._vnode_backrefs.add(vnode)


class SplitPartialVnode(BsearchPartialVnode):
    __slots__ = ('__weakref__',)
    def __init__(self, version, *, dnode=None):
        dnode = dnode or SplitPartialDnode()
        super().__init__(version, dnode=dnode)

        self.dnode._vnode_backrefs.add(self)

SplitPartialBackend.vnode_cls = SplitPartialVnode
