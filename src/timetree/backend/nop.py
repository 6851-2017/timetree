from .base import BaseBackend


class NOPBackend(BaseBackend):
    """ Timetree backend which doesn't support any persistence (no commits,
    only one head)
    """

    def __init__(self):
        class VNode:
            def __init__(self):
                self.values = dict()
        self.VNode = VNode
        self.base_commit = object()
        self.head = None

    def get_base_commit(self):
        """ Get the base commit, on which we can build new versions

        :return: An identifier for the base commit
        """
        return self.base_commit

    def commit(self, head, vnodes):
        """Commit is an illegal operation"""
        head, vnodes = super().commit(head, vnodes)
        raise NotImplementedError

    def branch(self, commit, vnodes, *args):
        """ Branch only once from the empty commit """
        sources = super().branch(commit, vnodes, *args)
        assert all(
            commit == self.base_commit and len(vnodes) == 0
            for commit, vnodes in sources)

        if self.head is not None:
            raise ValueError('NoPBackend only supports one head')
        self.head = object()

        return self.head, [[] for _ in sources]

    def new_node(self, head):
        """ Create a new vnode in the specific head

        :param version: The current version object
        :return: A new vnode in the current version
        """
        super().new_node(head)
        assert head == self.head()
        return self.VNode()

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

    def get_version(self, vnode):
        """ Get the version of a vnode

        :param vnode: Vnode to query
        :return: Version of the vnode
        """
        super().get_version(vnode)
        return self.head

    def is_head(self, version):
        """ Returns whether a version is a head or a commit

        :param version: Version to query
        :return: Boolean of True if it's a head and otherwise False
        """
        super().is_head(version)
        return version == self.head
