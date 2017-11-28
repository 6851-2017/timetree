from .base import BaseBackend
from .base import BaseVersion
from .base import BaseVnode


class CopyBackend(BaseBackend):
    """ Timetree backend which copies everything always

    Designed to be a reference implementation
    """

    def __init__(self):
        super().__init__()

    def commit(self, vnodes=None):
        vnodes = super().commit(vnodes)

        commit = CopyVersion(self, is_head=False)
        return commit, self._clone(vnodes, commit)

    def branch(self, vnodes=None):
        vnodes = super().branch(vnodes)

        head = CopyVersion(self, is_head=True)
        return head, self._clone(vnodes, head)

    def _clone(self, vnodes, version):
        """ Clone vnodes under a new version

        :param vnodes: Vnodes to clone
        :param version: New version
        :return: Mapping of vnodes
        """
        old_versions = {vnode.version for vnode in vnodes}

        node_maps = dict()
        for old_version in old_versions:
            node_map = {vnode: CopyVnode(version) for vnode in old_version.vnodes}
            for vnode, new_vnode in node_map.items():
                # Write in the new values
                new_vnode.values = {
                    k: node_map[v] if self.is_vnode(v) else v
                    for k, v in vnode.values.items()
                }
            version.vnodes.extend(node_map.values())
            node_maps[old_version] = node_map
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
