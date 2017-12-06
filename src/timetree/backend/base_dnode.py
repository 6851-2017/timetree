from abc import ABCMeta
from abc import abstractmethod

from .base_util import BaseCopyableVnode


class BaseDnode(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def get(self, field, version_num):
        pass

    @abstractmethod
    def set(self, field, value, version_num):
        pass

    @abstractmethod
    def delete(self, field, version_num):
        pass


class BaseDnodeBackedVnode(BaseCopyableVnode):
    __slots__ = ('dnode', )

    dnode_cls = BaseDnode  # Illegal

    def __init__(self, version, *, dnode=None):
        super().__init__(version)

        if dnode is not None:
            # Restore an old vnode
            self.dnode = dnode
            return

        self.dnode = self.dnode_cls()

    def get(self, field):
        super().get(field)
        result = self.dnode.get(field, self.version.version_num)
        if isinstance(result, self.dnode_cls):
            result = self.__class__(self.version, dnode=result)
        return result

    def set(self, field, value):
        super().set(field, value)
        if self.backend.is_vnode(value):
            value = value.dnode
        self.dnode.set(field, value, self.version.version_num)

    def delete(self, field):
        super().delete(field)
        self.dnode.delete(field, self.version.version_num)

    def copy(self, version):
        return self.__class__(version, dnode=self.dnode)

    def __eq__(self, other):
        return (self.version, self.dnode) == (other.version, other.dnode)

    def __hash__(self):
        return hash((self.version, self.dnode))
