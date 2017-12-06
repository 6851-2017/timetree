from .base_dnode import BaseDnode
from .base_dnode import BaseDnodeBackedVnode
from .base_linearized_full import BaseLinearizedFullBackend


class SplitLinearizedFullDnode(BaseDnode):
    __slots__ = ('start_version', 'end_version')

    _deleted_marker = object()

    def __init__(self, backend):
        super().__init__(backend)
        self.start_version = backend.v_0
        self.end_version = backend.v_inf
        raise NotImplementedError

    def get(self, field, version_num):
        if not self.start_version <= version_num < self.end_version:
            raise ValueError('version_num was invalid for this dnode')
        raise NotImplementedError

    def set(self, field, value, version_num):
        if not self.start_version <= version_num < self.end_version:
            raise ValueError('version_num was invalid for this dnode')
        raise NotImplementedError

    def delete(self, field, version_num):
        if not self.start_version <= version_num < self.end_version:
            raise ValueError('version_num was invalid for this dnode')
        self.set(field, self._deleted_marker, version_num)


class SplitLinearizedFullVnode(BaseDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = SplitLinearizedFullDnode


class SplitLinearizedFullBackend(BaseLinearizedFullBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = SplitLinearizedFullVnode
