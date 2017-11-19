from .base import BaseBackend


class CopyBackend(BaseBackend):
    """ Timetree backend which copies everything always

    Designed to be a reference implementation
    """

    def __init__(self):

        class Version:
            def __init__(self):
                self.vnodes = []

        class Commit(Version):
            def __init__(self):
                super().__init__()

        class Head(Version):
            def __init__(self):
                super().__init__()

        class VNode:
            def __init__(self, version):
                self.version = version
                self.values = dict()

        self.Head = Head
        self.Commit = Commit
        self.Version = Version
        self.VNode = VNode

        self.base_commit = Commit()

    def get_base_commit(self):
        """ Get the base commit, on which we can build new versions

        :return: An identifier for the base commit
        """
        return self.base_commit

    def new_node(self, head):
        """ Create a new vnode in the specific head

        :param version: The current version object
        :return: A new vnode in the current version
        """
        super().new_node(head)
        vnode = self.VNode(head)
        head.vnodes.append(vnode)
        return vnode

    def get(self, vnode, field):
        """ Get a field of a vnode

        :param vnode: Vnode to access
        :param field: Field name
        :return: Field value
        :raises KeyError: Field not found in vnode
        """
        super().get(vnode, field)
        if field not in vnode.values:
            raise KeyError
        return vnode.values[field]

    def _is_vnode(self, value):
        return isinstance(value, self.VNode)

    def set(self, vnode, field, value):
        """ Set a field of a vnode

        :param vnode: Vnode to modify
        :param field: Field name
        :param value: New value to set
            Must be in the same version if it's also a vnode.
        :return: None
        :raises ValueError: Value is a vnode but isn't at the same version
        """
        super().set(vnode, field, value)
        vnode.values[field] = value

    def delete(self, vnode, field):
        """ Delete a field of a vnode

        :param vnode: Vnode to delete from
        :param field: Field name
        :return: None
        :raises KeyError: Field not found in vnode
        """
        super().delete(vnode, field)
        if field not in vnode.values:
            raise KeyError
        del vnode.values[field]

    def _clone(self, vnodes, version):
        """ Clone vnodes under a new version

        :param vnodes: Vnodes to clone
        :param version: New version
        :return: Mapping of vnodes
        """
        node_map = {vnode: self.VNode(version) for vnode in vnodes}
        for vnode, new_vnode in node_map.items():
            # Write in the new values
            new_vnode.values = {
                k: node_map[v] if self._is_vnode(v) else v
                for k, v in vnode.values.items()
            }
        return node_map

    def commit(self, head, vnodes):
        """Commit is an illegal operation"""
        head, vnodes = super().commit(head, vnodes)

        commit = self.Commit()
        node_map = self._clone(head.vnodes, commit)
        return commit, [node_map[vnode] for vnode in vnodes]

    def branch(self, commit, vnodes, *args):
        """ Branch only once from the empty commit """
        sources = super().branch(commit, vnodes, *args)

        head = self.Head()

        result = []
        for commit, vnodes in sources:
            node_map = self._clone(commit.vnodes, head)
            result.append([node_map[vnode] for vnode in vnodes])

        return head, result

    def get_version(self, vnode):
        """ Get the version of a vnode

        :param vnode: Vnode to query
        :return: Version of the vnode
        """
        super().get_version(vnode)
        return vnode.version

    def is_head(self, version):
        """ Returns whether a version is a head or a commit

        :param version: Version to query
        :return: Boolean of True if it's a head and otherwise False
        """
        super().is_head(version)
        return isinstance(version, self.Head)
