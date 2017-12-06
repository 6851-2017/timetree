from abc import ABCMeta

from .base import BaseVersion
from .base_util import BaseCopyableVnode
from .base_util import BaseDivergentBackend


class BasePartialBackend(BaseDivergentBackend, metaclass=ABCMeta):
    """ (Optional) base class for partially persistent backends

    Handles most of the heavy lifting of version management. The user only
    needs to implement the Vnode and set Backend.vnode_cls to it.

    _commit just uses shallow copies to clone vnodes; if this isn't correct,
    override _commit.
    """
    __slots__ = ('head')

    vnode_cls = BaseCopyableVnode  # Type of vnodes to create, should be Copyable

    def __init__(self):
        self.head = PartialHead(self, self.vnode_cls)

    def _commit(self, vnodes):
        """ Default just makes a shallow copy of vnodes and returns it """
        super()._commit(vnodes)

        commit = PartialCommit(self, self.head.version_num)
        result = []
        for vnode in vnodes:
            new_vnode = vnode.copy(commit)
            result.append(new_vnode)

        self.head.version_num += 1

        return commit, result

    def _branch(self, vnodes):
        super()._branch(vnodes)

        if not vnodes:
            return self.head, []

        raise NotImplementedError("Partially persistent backends cannot branch")


class BasePartialVersion(BaseVersion, metaclass=ABCMeta):
    __slots__ = ()


class PartialHead(BasePartialVersion):
    __slots__ = ('vnode_cls', 'version_num', )

    def __init__(self, backend, vnode_cls):
        super().__init__(backend, is_head=True)
        self.vnode_cls = vnode_cls
        self.version_num = 0

    def new_node(self):
        return self.vnode_cls(self)


class PartialCommit(BasePartialVersion):
    __slots__ = ('version_num', )

    def __init__(self, backend, version_num):
        super().__init__(backend, is_head=False)
        self.version_num = version_num

    def new_node(self):
        raise ValueError("Can't create a node from a commit")
