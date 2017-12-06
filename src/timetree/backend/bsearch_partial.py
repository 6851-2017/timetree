from collections import defaultdict
from collections import namedtuple

from .base_dnode import BaseDnode
from .base_dnode import BaseDnodeBackedVnode
from .base_partial import BasePartialBackend

Mod = namedtuple('Mod', ['version_num', 'value'])


class BsearchPartialDnode(BaseDnode):
    __slots__ = ('mods_dict',)

    _deleted_marker = object()

    def __init__(self, backend):
        super().__init__(backend)
        self.mods_dict = defaultdict(list)

    def get(self, field, version_num):
        if field not in self.mods_dict:
            raise KeyError('Never created')
        mods = self.mods_dict[field]

        assert mods, "Mods shouldn't be empty if it's in the dict"

        # OPTIMIZATION: Fast-path for present-time queries
        if mods[-1].version_num <= version_num:
            result = mods[-1].value
        else:
            # Binary search to find the last mod <= self.version_num
            mi = -1
            ma = len(mods)
            while ma - mi > 1:
                md = (mi + ma) // 2
                if mods[md].version_num <= version_num:
                    mi = md
                else:
                    ma = md

            if mi == -1:
                raise KeyError('Not created yet')

            result = mods[mi].value

        if result is self._deleted_marker:
            raise KeyError('Field deleted')

        return result

    def set(self, field, value, version_num):
        mods = self.mods_dict[field]
        if not mods or mods[-1].version_num <= version_num:
            mods.append(Mod(version_num, value))
        else:
            raise ValueError("Can only add mods at the end")

    def delete(self, field, version_num):
        self.set(field, self._deleted_marker, version_num)


class BsearchPartialVnode(BaseDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = BsearchPartialDnode


class BsearchPartialBackend(BasePartialBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = BsearchPartialVnode
