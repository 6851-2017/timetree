from collections import defaultdict

from .base_partial import BasePartialBackend
from .base_partial import BasePartialVnode


class BsearchPartialBackend(BasePartialBackend):
    __slots__ = ()


class BsearchPartialDnode:
    __slots__ = ('mods_dict',)

    _deleted_marker = object()

    def __init__(self):
        self.mods_dict = defaultdict(list)

    def get(self, field, version_num):
        if field not in self.mods_dict:
            raise KeyError('Never created')
        mods = self.mods_dict[field]

        assert mods, "Mods shouldn't be empty if it's in the dict"

        # OPTIMIZATION: Fast-path for present-time queries
        if mods[-1][0] <= version_num:
            return mods[-1][1]

        # Binary search to find the last mod <= self.version_num
        mi = -1
        ma = len(mods)
        while ma - mi > 1:
            md = (mi + ma) // 2
            if mods[md][0] <= version_num:
                mi = md
            else:
                ma = md

        if mi == -1:
            raise KeyError('Not created yet')

        result = mods[mi][1]

        if result is self._deleted_marker:
            raise KeyError('Field deleted')

        return result

    def set(self, field, value, version_num):
        self.mods_dict[field].append((version_num, value))

    def delete(self, field, version_num):
        self.mods_dict[field].append((version_num, self._deleted_marker))


class BsearchPartialVnode(BasePartialVnode):
    __slots__ = ('dnode', )

    def __init__(self, version, *, dnode=None):
        super().__init__(version)

        if dnode is not None:
            # Restore an old vnode
            self.dnode = dnode
            return

        self.dnode = BsearchPartialDnode()

    def get(self, field):
        super().get(field)
        result = self.dnode.get(field, self.version_num)
        if isinstance(result, BsearchPartialDnode):
            result = BsearchPartialVnode(self.version, dnode=result)
        return result

    def set(self, field, value):
        super().set(field, value)
        if self.backend.is_vnode(value):
            value = value.dnode
        self.dnode.set(field, value, self.version_num)

    def delete(self, field):
        super().delete(field)
        self.dnode.delete(field, self.version_num)

    def __eq__(self, other):
        return (self.version, self.dnode) == (other.version, other.dnode)

    def __hash__(self):
        return hash((self.version, self.dnode))


# Set the vnode class of the backend
BsearchPartialBackend.vnode_cls = BsearchPartialVnode
