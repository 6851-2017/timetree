from abc import ABCMeta
from abc import abstractmethod

from .base import BaseBackend
from .base import BaseVnode


class BaseCopyableVnode(BaseVnode, metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def copy(self, new_version):
        """ We guarantee the new_version and the current version correspond
        to the same represented object
        """
        pass


class BaseDivergentBackend(BaseBackend, metaclass=ABCMeta):
    """ (Optional) base class for non-confluent backends
    """

    __slots__ = ()

    @abstractmethod
    def _branch(self, vnodes):
        super()._branch(vnodes)

        if vnodes:
            commit = vnodes[0].version
            if not all(vnode.version == commit for vnode in vnodes):
                raise NotImplementedError('Vnodes must all have the same version')
