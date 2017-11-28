from .base import BaseBackend, BaseVersion, BaseVnode
from collections import defaultdict


class CopyBackend(BaseBackend):
    """ Timetree backend which copies everything always

    Designed to be a reference implementation
    """

    def __init__(self):
        super().__init__()

    def commit(self, vnodes):
        vnodes = super().commit(vnodes)

        commit = CopyVersion(self, is_head=False)
        return commit, self._clone(vnodes, commit)

    def branch(self, vnodes):
        vnodes = super().branch(vnodes)

        head = CopyVersion(self, is_head=True)
        return head, self._clone(vnodes, head)

    def _clone(self, vnodes, version):
        """ Clone vnodes under a new version

        :param vnodes: Vnodes to clone
        :param version: New version
        :return: Mapping of vnodes
        """
        vnodes_by_version = defaultdict(set)
        for vnode in vnodes:
            vnodes_by_version[vnode.version].add(vnode)

        node_maps = dict()
        for _version, _vnodes in vnodes_by_version.items():
            node_map = {vnode: CopyVnode(version) for vnode in _vnodes}
            for vnode, new_vnode in node_map.items():
                # Write in the new values
                new_vnode.values = {
                    k: node_map[v] if self.is_vnode(v) else v
                    for k, v in vnode.values.items()
                }
            node_maps[_version] = node_map
        return [node_maps[vnode.version][vnode] for vnode in vnodes]


class CopyVersion(BaseVersion):
    __slots__ = ('backend', 'is_head', 'vnodes')

    def __init__(self, backend, is_head):
        super().__init__()
        self.backend = backend
        self.is_head = is_head
        self.vnodes = []

    def new_node(self):
        super().new_node()
        vnode = CopyVnode(self)
        self.vnodes.append(vnode)
        return vnode


class CopyVnode(BaseVnode):
    __slots__ = ('version', 'values')

    def __init__(self, version):
        self.version = version
        self.values = dict()

    def get(self, field):
        super().get(field)
        if field not in self.values:
            raise KeyError
        return self.values[field]

    def set(self, field, value):
        super().set(field, value)
        self.values[field] = value

    def delete(self, field):
        super().delete(field)
        if field not in self.values:
            raise KeyError
        del self.values[field]
