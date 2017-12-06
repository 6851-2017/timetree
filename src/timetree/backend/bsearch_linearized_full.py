from collections import defaultdict
from collections import namedtuple

from .base_dnode import BaseDnode
from .base_dnode import BaseDnodeBackedVnode
from .base_linearized_full import BaseLinearizedFullBackend

Mod = namedtuple('Mod', ['version_num', 'value'])


class BsearchLinearizedFullDnode(BaseDnode):
    __slots__ = ('mods_dict',)

    _deleted_marker = object()

    def __init__(self, backend):
        super().__init__(backend)
        self.mods_dict = defaultdict(list)

    def get(self, field, version_num):
        super().get(field, version_num)

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
        super().set(field, value, version_num)

        new_mod = Mod(version_num, value)
        mods = self.mods_dict[field]
        if not mods or mods[-1].version_num < version_num:
            mods.append(new_mod)
        else:
            mi = -1
            ma = len(mods)
            while ma - mi > 1:
                md = (mi + ma) // 2
                if mods[md].version_num <= version_num:
                    mi = md
                else:
                    ma = md
            assert mi == -1 or mods[mi].version_num <= version_num
            assert ma == len(mods) or mods[ma].version_num > version_num
            assert ma == mi + 1
            if ma == len(mods) or mods[ma].version_num > version_num.next:
                prev_value = mods[mi].value if mi >= 0 else self._deleted_marker
                succ_mod = Mod(version_num.next, prev_value)
                mods.insert(ma, succ_mod)
            if mi >= 0 and mods[mi].version_num == version_num:
                mods[mi] = new_mod
            else:
                mods.insert(ma, new_mod)

    def delete(self, field, version_num):
        super().delete(field, version_num)
        self.set(field, self._deleted_marker, version_num)


class BsearchLinearizedFullVnode(BaseDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = BsearchLinearizedFullDnode


class BsearchLinearizedFullBackend(BaseLinearizedFullBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = BsearchLinearizedFullVnode
