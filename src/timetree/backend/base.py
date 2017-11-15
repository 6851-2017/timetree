from abc import ABCMeta
from abc import abstractmethod


class BaseBackend(metaclass=ABCMeta):
    """ Abstract base class for persistence backends

    The timetree backend operates on directed acyclic graph (DAG) of
    "versions", each of which is a pointer machine of "vnodes" (virtual or
    versioned nodes). Vnodes can each have fields keyed by strings, which can
    be inserted, set and deleted. Fields must point to other vnodes in the
    same version, or external (ideally immutable) data not in the timetree.
    Because we are working with only persistence, vnodes can only be modified
    if their corresponding version is a terminal node (a leaf in a tree).
    Thus, we can think of modifiable (leaf) versions and frozen (internal)
    versions.

    Initially, the tree contains only a single frozen base version. To create
    new versions, we provide the :py:meth:`.commit` method, which freezes
    (marks unmodifiable) a current version, and creates a new modifiable
    version with an identical pointer machine to the previous version. In
    particular, we (implicitly) create a copy of each vnode and set all
    pointers to refer to these new copies. To retrieve or use the new copies,
    call the :py:meth:`.upgrade_version` method on the old vnodes.

    In backends that support confluent persistence, :py:meth:`.commit` may
    actually take multiple versions: it creates copies of all nodes in each
    version passed in. In essence, it creates the disjoint union of all
    passed in versions.
    """

    @abstractmethod
    def get_base_version(self):
        """ Get the frozen base version, on which we can build new versions

        :return: An identifier for the base version
        """
        return 0

    @abstractmethod
    def new_node(self, version):
        """ Create a new vnode in the specific version

        :param version: The current version object
        :return: A new vnode in the current version
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, vnode, field):
        """ Get a field of a vnode

        :param vnode: Vnode to access
        :param field: Field name
        :return: Field value
        :raises KeyError: Field not found in vnode
        """
        raise NotImplementedError

    @abstractmethod
    def set(self, vnode, field, value):
        """ Set a field of a vnode

        :param vnode: Vnode to modify
        :param field: Field name
        :param value: New value to set
            Must be in the same version if it's also a vnode.
        :return: None
        :raises ValueError: Value is a vnode but isn't at the same version
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, vnode, field):
        """ Delete a field of a vnode

        :param vnode: Vnode to delete from
        :param field: Field name
        :return: None
        :raises KeyError: Field not found in vnode
        """
        raise NotImplementedError

    @abstractmethod
    def commit(self, *version):
        """ Create a new commit based on the given version(s)

        Mark the current versions as frozen, and create copies of all their
        vnodes in the new version. The new vnodes can be accessed with
        :py:meth:`.upgrade_version`.

        :param version: Varargs for versions to base the commit off of
        :return: New version identifier
        """
        raise NotImplementedError

    @abstractmethod
    def upgrade_version(self, vnode, new_version):
        """ Upgrade the version of a vnode to the copy of it in new_version.

        Raises an error if vnode's version isn't an ancestor of new_version,
        or if vnode's copy in new_version has already been modified.

        :param vnode: Vnode to upgrade
        :param new_version: New version to upgrade to
        :return: The copy of vnode at new_version
        :raises ValueError: Upgrade is invalid (see above)
        """
        raise NotImplementedError

    @abstractmethod
    def get_version(self, vnode):
        """ Get the version of a vnode

        :param vnode: Vnode to query
        :return: Version of the vnode
        """
        raise NotImplementedError
