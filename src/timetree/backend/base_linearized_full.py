from abc import ABCMeta

from .base import BaseVersion
from .base import BaseVnode
from .base_dnode import BaseDnodeBackedVnode
from .base_util import BaseCopyableVnode
from .base_util import BaseDivergentBackend
from .util.order_maintenance import FastLabelerList
from .util.order_maintenance import FastLabelerNode


class BaseLinearizedFullBackend(BaseDivergentBackend):
    __slots__ = ('version_list', 'base_commit')

    vnode_cls = BaseCopyableVnode  # Type of vnodes to create, should be Copyable

    def __init__(self):
        self.version_list = FastLabelerList()
        # Points to the head of the version list
        self.base_commit = LinearizedFullCommit(self, self.version_list)

    def _commit(self, vnodes):
        """ Default just makes a shallow copy of vnodes and returns it """
        super()._commit(vnodes)

        if not vnodes:
            return self.base_commit, []

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

        commit = vnodes[0].version if vnodes else self.base_commit

        version_num = commit.version_num

        # Make new versions (and un-version)
        new_version_num = FastLabelerNode()
        new_un_version_num = FastLabelerNode()
        self.version_list.insert_after(version_num, new_version_num)
        self.version_list.insert_after(new_version_num, new_un_version_num)

        head = LinearizedFullHead(self, new_version_num, new_un_version_num, self.vnode_cls)

        result = []
        for vnode in vnodes:
            new_vnode = vnode.copy(head)
            result.append(new_vnode)

        return head, result


class BaseLinearizedFullVersion(BaseVersion, metaclass=ABCMeta):
    __slots__ = ()


class LinearizedFullHead(BaseVersion):
    __slots__ = ('vnode_cls', 'version_num', 'un_version_num',)

    def __init__(self, backend, version_num, un_version_num, vnode_cls):
        super().__init__(backend, is_head=True)
        self.vnode_cls = vnode_cls
        self.version_num = version_num
        self.un_version_num = un_version_num
        assert not version_num.is_head
        assert not un_version_num.is_head

    def new_node(self):
        return self.vnode_cls(self)


class LinearizedFullCommit(BaseVersion):
    __slots__ = ('version_num',)

    def __init__(self, backend, version_num):
        super().__init__(backend, is_head=False)
        self.version_num = version_num

    def new_node(self):
        raise ValueError("Can't create a node from a commit")


class BaseLinearizedDnodeBackedVnode(BaseDnodeBackedVnode):
    __slots__ = ('dnode',)

    def _save_old(self, field):
        try:
            old_value = self.dnode.get(field, self.version.version_num)
            self.dnode.set(field, old_value, self.version.un_version_num)
        except KeyError:
            self.dnode.delete(field, self.version.un_version_num)

    def set(self, field, value):
        # Don't call BaseDnodeBackedVnode.set(), which does the actual thing,
        #  just do the validation
        BaseVnode.set(self, field, value)
        super(BaseDnodeBackedVnode, self).set(field, value)

        self._save_old(field)

        super().set(field, value)

    def delete(self, field):
        # Don't call BaseDnodeBackedVnode.delete(), which does the actual thing,
        #  just do the validation
        BaseVnode.delete(self, field)

        self._save_old(field)

        super().delete(field)
