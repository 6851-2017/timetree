from abc import ABCMeta
from abc import abstractmethod


class BaseBackend(metaclass=ABCMeta):
    """ Abstract base class for persistence backends

    Timetree's general goal is to express persistent data structures:
    structures in which we can "travel back in time" to a previous state. To
    do this, we'll represent the state of the data structure at each
    particular "point in time" or "version" as a separate pointer machine of
    "vnodes" (virtual or versioned nodes), represented by classes
    `BaseVersion` and `BaseVnode`. Vnodes are each bound to a particular
    version, and each have fields keyed by strings, which can be manipulated
    with :py:meth:`.get`, :py:meth:`.set` and :py:meth:`.delete`. Fields may
    point to other vnodes in the same machine or to external (ideally
    immutable) data not in the timetree, but *not* to other versions in the
    timetree.

    The structure of the versions can take on various forms, but most
    generally, they form a DAG. Edges in the DAG represent implicit copies:
    we construct each new pointer machine as some set of edits
    (`set`s/`delete`s) on top of the union of copies of some other existing
    pointer machines, which are the parents in the DAG. (This describes
    confluent persistence. In the case of fully persistent data structures,
    the versions form a tree, as each new machine is an edit of only a
    single previous version; machines at different times cannot merge.)

    Because we are working with only persistence, vnodes can only be modified
    if their corresponding version is a terminal node (a leaf in a tree) in
    the DAG. Thus, we can think of modifiable (terminal/leaf) versions and
    frozen (internal) versions. From here on, we'll call the modifiable
    versions "heads", and frozen versions "commits". Note that vnodes can be
    bound to heads or commits. We also won't enforce that commits must be
    internal, though heads always must be leaves.

    Initially, the tree contains only a single base commit which is an empty
    pointer machine. We provide two different operations to create new versions
    and heads.

    The first is :py:meth:`.branch(vnodes)`, which takes a list of vnodes.
    Branch returns a new head based off of all commits of vnodes given,
    and returns vnodes bound to the new head corresponding to copies of the
    input vnodes.

    Second, we have :py:meth:`.commit(vnodes)`. This takes a list of vnodes
    bound to a single head version and creates a (frozen) copy of it (a
    commit). This commit shares the same parents as the head in the version
    DAG, and we update the head's parent to be only the newly created commit
    (we split the head into an edge). Alternatively, we mark the head as
    frozen, create a new head on top, and update all vnodes originally bound
    to head to bind to the new head. We return the commit, as well as
    corresponding copies of argument `vnodes`, but rebound to commit.

    To make the operations clearer, we show an alternative view of the version
    pool. We consider the set of only commits. Then, a "head" is a working
    copy of (one or more) commit(s), which we can muck around with and edit.
    `branch` creates a new head and lets us access its vnodes, while `commit`
    takes an existing head and saves a copy of the current state as a commit.
    In this sense, "heads" and "commits" somewhat match Git's usage of these
    words.
    """

    __slots__ = ()

    @abstractmethod
    def is_vnode(self, value):
        """ Check if a value is a vnode of this backend

        :param value: The value to check
        :return: True if it is a vnode
        """

    @abstractmethod
    def commit(self, vnodes=None):
        """ Create a new commit based on the given head

        In different views, this can be:
            - Split the current head in the version DAG into a commit and a
            head.
            - Change the head to a commit, create a new head on top,
            and implicitly rebind all references to head to the new head.
            - Add a copy of head as a commit to the pool of commits.

        If vnodes is empty or not given, then the new commit is the base commit.

        :param vnodes: Vnodes which we would like references to; must be
        bound to the same head
        :return: Reference to the new commit, a list of `vnodes` rebound to it
        """
        # The default implementation sanitize vnodes into a list and
        # validates things
        if vnodes is None:
            vnodes = []
        else:
            vnodes = list(vnodes)

        if not all(self.is_vnode(vnode) for vnode in vnodes):
            raise ValueError('Invalid vnode in commit')

        if vnodes:
            head = vnodes[0].version
            if not all(vnode.version == head for vnode in vnodes):
                raise ValueError('Vnodes must all have the same version')
            if not head.version.is_head:
                raise ValueError('Vnode version not a head')

        return vnodes

    @abstractmethod
    def branch(self, vnodes=None):
        """ Create a new head based on the given vnodes

        The head's pointer machine is the disjoint union of the pointer
        machines of the originating commits of the given vnodes.

        If vnodes is empty, then create a new branch based off of the base commit.

        :param vnodes: Vnodes which we would like references to; must all be
        bound to commits
        :return: Reference to the new head and a list of `vnodes` rebound to it
        """
        # The default implementation sanitize vnodes into a list and
        # validates things
        if vnodes is None:
            vnodes = []
        else:
            vnodes = list(vnodes)

        if not all(self.is_vnode(vnode) for vnode in vnodes):
            raise ValueError('Invalid vnode in branch')

        if not all(vnode.version.is_commit for vnode in vnodes):
            raise ValueError('Vnode is not a commit')

        return vnodes


class BaseVersion(metaclass=ABCMeta):
    """ Abstract base class for versions of backends """

    __slots__ = ()

    @property
    def backend(self):
        """ Return the backend of this vnode """
        raise NotImplementedError()

    @abstractmethod
    def new_node(self):
        """ Create a new vnode in this version

        Version must be a head

        :return: A new vnode in the version
        """
        if not self.is_head:
            raise ValueError("Can only create in head versions")

    @property
    @abstractmethod
    def is_head(self):
        """ Returns whether a version is a head or a commit

        :return: Boolean of True if it's a head and otherwise False
        """

    @property
    def is_commit(self):
        """ Returns whether a version is a commit or a head

        :return: Boolean of True if it's a commit and otherwise False
        """
        return not self.is_head


class BaseVnode(metaclass=ABCMeta):
    """ Abstract base class for vnodes of backends """
    __slots__ = ()

    @property
    def backend(self):
        """ Return the backend of this vnode """
        return self.version.backend

    @property
    def version(self):
        """ Return the version of this vnode """
        raise NotImplementedError()

    @abstractmethod
    def get(self, field):
        """ Get a field of a vnode

        :param field: Field name
        :return: Field value
        :raises KeyError: Field not found in vnode
        """

    @abstractmethod
    def set(self, field, value):
        """ Set a field of a vnode

        :param field: Field name
        :param value: New value to set
            Must be in the same version if it's also a vnode.
        :return: None
        :raises ValueError: Value is a vnode but isn't at the same version
        """
        if not self.version.is_head:
            raise ValueError("Can only set in head versions")
        if self.backend.is_vnode(value):
            if self.version != value.version:
                raise ValueError("Mismatched versions")

    @abstractmethod
    def delete(self, field):
        """ Delete a field of a vnode

        :param field: Field name
        :return: None
        :raises KeyError: Field not found in vnode
        """
        if not self.version.is_head:
            raise ValueError("Can only delete from head versions")

    def commit(self):
        """ Commit this vnode and return the new vnode

        Equivalent to extracting the vnode from self.backend.commit:
            return self.backend.commit([self])[1][0]
        """
        new_version, [new_vnode] = self.backend.commit([self])
        return new_vnode

    def branch(self):
        """ Branch from this vnode and return the new vnode

        Equivalent to extracting the vnode from self.backend.branch:
            return self.backend.branch([self])[1][0]
        """
        new_version, [new_vnode] = self.backend.branch([self])
        return new_vnode
