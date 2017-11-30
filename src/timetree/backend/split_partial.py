from collections import defaultdict
import weakref

from .bsearch_partial import BsearchPartialBackend
from .bsearch_partial import BsearchPartialDnode
from .bsearch_partial import BsearchPartialVnode

class SplitPartialBackend(BsearchPartialBackend):
    __slots__ = ()

class SplitPartialDnode(BsearchPartialDnode):
    __slots__ = ('_field_backrefs', '_vnode_backrefs')

    def __init__(self):
        super().__init__()
        self._field_backrefs = weakref.WeakSet()
        self._vnode_backrefs = weakref.WeakSet()

    def set(self, field, value, version_num):
        old_value = self.get(version_num)

        # delete old backref
        if self.is_vnode(old_value):
            old_value._field_backrefs.remove((weakref.ref(self), field))

        super().set(field, value, version_num)

        # add new backref
        if self.is_vnode(value):
            value._field_backrefs.add((self, field))

        # split if necessary
        if len(self.mods_dict[field]) > 64: #TODO: better split condition
            new_dnode = SplitPartialDnode()

            for field, mods in self.mods_dict.items():
                new_dnode.mods_dict[field] = mods[-1]

            for dnode, field in _field_backrefs:
                dnode.set(field, new_dnode, version_num)

            for vnode in _vnode_backrefs:
                vnode.dnode = new_dnode


class SplitPartialVnode(BsearchPartialVnode):
    __slots__ = ()
    def __init__(self, version, *, dnode=None):
        super().__init__(version, dnode=None)
        if dnode != None:
            dnode._vnode_backrefs.add(self)

BsearchPartialBackend.vnode_cls = SplitPartialVnode