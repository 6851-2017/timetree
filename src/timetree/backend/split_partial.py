import weakref

from .base_partial import BasePartialVersion
from .bsearch_partial import BsearchPartialBackend
from .bsearch_partial import BsearchPartialDnode
from .bsearch_partial import BsearchPartialVnode


class SplitPartialBackend(BsearchPartialBackend):
    __slots__ = ()


class SplitPartialDnode(BsearchPartialDnode):
    __slots__ = ('_field_backrefs', '_vnode_backrefs', '__weakref__')

    def __init__(self):
        super().__init__()
        self._field_backrefs = weakref.WeakKeyDictionary()  # This should be a weak key default dict
        self._vnode_backrefs = weakref.WeakSet()

    def _add_field_backref(self, dnode, field):
        self._field_backrefs[dnode] = self._field_backrefs.get(dnode, set())
        self._field_backrefs[dnode].add(field)

    def _remove_field_backref(self, dnode, field):
        self._field_backrefs[dnode].remove(field)
        if not self._field_backrefs[dnode]:
            del self._field_backrefs[dnode]

    def set(self, field, value, version_num):
        if len(self.mods_dict[field]) > 0:
            # delete old backref
            old_value = self.get(field, version_num)
            if isinstance(old_value, SplitPartialDnode):
                old_value._remove_field_backref(self, field)

        super().set(field, value, version_num)

        # add new backref
        if isinstance(value, SplitPartialDnode):
            value._add_field_backref(self, field)

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
                    value._remove_field_backref(self, field)
                    value._add_field_backref(new_dnode, field)

            # update head vnodes
            for vnode in set(self._vnode_backrefs):
                if vnode.version.is_head:
                    assert vnode.version.version_num == version_num
                    self._vnode_backrefs.remove(vnode)
                    vnode.dnode = new_dnode
                    new_dnode._vnode_backrefs.add(vnode)

            # update forward references to this node, possibly causing chain reactions
            while self._field_backrefs:
                dnode = next(iter(self._field_backrefs))
                field = next(iter(self._field_backrefs[dnode]))
                dnode.set(field, new_dnode, version_num)


class SplitPartialVnode(BsearchPartialVnode):
    __slots__ = ('__weakref__',)

    def __init__(self, version, *, dnode=None):
        dnode = dnode or SplitPartialDnode()
        super().__init__(version, dnode=dnode)

        self.dnode._vnode_backrefs.add(self)

    def __repr__(self):
        return 'SplitPartialVnode<%s, %s>' % (self.version.version_num, self.dnode)


SplitPartialBackend.vnode_cls = SplitPartialVnode
