from .base_dnode import BaseDnode
from .base_dnode import BaseDnodeBackedVnode
from .base_linearized_full import BaseLinearizedFullBackend
from .util.predecessor import SplayPredecessorDict


class BSTLinearizedFullDnode(BaseDnode):
    __slots__ = ('mods_dict',)

    _deleted_marker = object()

    def __init__(self, backend):
        super().__init__(backend)
        self.mods_dict = {}

    def get(self, field, version_num):
        super().get(field, version_num)

        if field not in self.mods_dict:
            raise KeyError('Never created')
        mods = self.mods_dict[field]

        try:
            result = mods.get_pred(version_num)
        except KeyError as e:
            raise RuntimeError('No earliest version in mod_dict') from e

        if result is self._deleted_marker:
            raise KeyError('Field deleted')

        return result

    def set(self, field, value, version_num):
        super().set(field, value, version_num)

        if field not in self.mods_dict:
            mods = SplayPredecessorDict()
            mods.set(self.backend.v_0, self._deleted_marker)
            self.mods_dict[field] = mods
        else:
            mods = self.mods_dict[field]

        old_val = mods.get_pred(version_num.next)
        mods.set(version_num, value)
        mods.set(version_num.next, old_val)

    def delete(self, field, version_num):
        super().delete(field, version_num)
        self.set(field, self._deleted_marker, version_num)


class BSTLinearizedFullVnode(BaseDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = BSTLinearizedFullDnode


class BSTLinearizedFullBackend(BaseLinearizedFullBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = BSTLinearizedFullVnode
