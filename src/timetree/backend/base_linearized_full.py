from abc import ABCMeta

from .base import BaseVersion
from .base_util import BaseCopyableVnode
from .base_util import BaseDivergentBackend
from .util.order_maintenance import FastLabelerList
from .util.order_maintenance import FastLabelerNode


class BaseLinearizedFullBackend(BaseDivergentBackend):
    __slots__ = ('version_list', 'v_0', 'v_inf')

    vnode_cls = BaseCopyableVnode  # Type of vnodes to create, should be Copyable

    def __init__(self):
        self.version_list = FastLabelerList()
        self.v_0 = FastLabelerNode()
        self.v_inf = FastLabelerNode()
        self.version_list.insert_after(None, self.v_0)
        self.version_list.insert_after(self.v_0, self.v_inf)

    def _commit(self, vnodes):
        """ Default just makes a shallow copy of vnodes and returns it """
        super()._commit(vnodes)

        if not vnodes:
            return LinearizedFullCommit(self, self.v_0), []

        head = vnodes[0].version
        version_num = head.version_num
        commit = LinearizedFullCommit(self, version_num)
        result = []
        for vnode in vnodes:
            new_vnode = vnode.copy(commit)
            result.append(new_vnode)

        new_version_num = FastLabelerNode()
        self.version_list.insert_after(version_num, new_version_num)
        head.version_num = new_version_num

        return commit, result

    def _branch(self, vnodes):
        super()._branch(vnodes)

        version_num = vnodes[0].version.version_num if vnodes else self.v_0

        # Make new versions (and un-version)
        new_version_num = FastLabelerNode()
        self.version_list.insert_after(version_num, new_version_num)

        head = LinearizedFullHead(self, new_version_num, self.vnode_cls)

        result = []
        for vnode in vnodes:
            new_vnode = vnode.copy(head)
            result.append(new_vnode)

        return head, result


class BaseLinearizedFullVersion(BaseVersion, metaclass=ABCMeta):
    __slots__ = ()


class LinearizedFullHead(BaseVersion):
    __slots__ = ('vnode_cls', 'version_num',)

    def __init__(self, backend, version_num, vnode_cls):
        super().__init__(backend, is_head=True)
        self.vnode_cls = vnode_cls
        self.version_num = version_num
        # Make sure that the version number and its successor aren't the
        # endpoint of the versions
        assert version_num.is_node and version_num.next.is_node

    def new_node(self):
        return self.vnode_cls(self)


class LinearizedFullCommit(BaseVersion):
    __slots__ = ('version_num',)

    def __init__(self, backend, version_num):
        super().__init__(backend, is_head=False)
        self.version_num = version_num

    def new_node(self):
        raise ValueError("Can't create a node from a commit")
