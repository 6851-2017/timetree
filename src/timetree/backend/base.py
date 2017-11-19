from abc import ABCMeta
from abc import abstractmethod


class BaseBackend(metaclass=ABCMeta):
    """ Abstract base class for persistence backends

    Timetree's general goal is to express persistent data structures:
    structures in which we can "travel back in time" to a previous state. To
    do this, we'll represent the state of the data structure at each
    particular "point in time" or "version" as a separate pointer
    machine of "vnodes" (virtual or versioned nodes). Vnodes are each bound
    to a particular version, and each have fields keyed by strings, which can
    be manipulated with :py:meth:`.get`, :py:meth:`.set` and
    :py:meth:`.delete`. Fields may point to other vnodes in the same machine
    or to external (ideally immutable) data not in the timetree, but *not* to
    other versions in the timetree.

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

    The first is :py:meth:`.branch(commits, vnodes)`, which takes a commit or a
    list of commits, as well as a list of vnodes bound to those commits.
    Branch returns a new head based off of all commits given, and returns
    vnodes bound to the new head corresponding to copies of the input vnodes.

    Second, we have :py:meth:`.commit(head, vnodes)`. This takes a single
    head version and creates a (frozen) copy of it (a commit). This commit
    shares the same parents as the head in the version DAG, and we update the
    head's parent to be only the newly created commit (we split the head into
    an edge). Alternatively, we mark the head as frozen, create a new head on
    top, and update all vnodes originally bound to head to bind to the new
    head. We return the commit, as well as corresponding copies of argument
    `vnodes`, but rebound to commit.

    To make the operations clearer, we show an alternative view of the version
    pool. We consider the set of only commits. Then, a "head" is a working
    copy of (one or more) commit(s), which we can muck around with and edit.
    `branch` creates a new head and lets us access its vnodes, while `commit`
    takes an existing head and saves a copy of the current state as a commit.
    In this sense, "heads" and "commits" somewhat match Git's usage of these
    words.
    """

    @abstractmethod
    def get_base_commit(self):
        """ Get the base commit, on which we can build new versions

        :return: An identifier for the base commit
        """

    @abstractmethod
    def new_node(self, head):
        """ Create a new vnode in the specific head version

        :param head: The head version
        :return: A new vnode in the head version
        """
        if not self.is_head(head):
            raise ValueError("Can only create in head versions")

    @abstractmethod
    def get(self, vnode, field):
        """ Get a field of a vnode

        :param vnode: Vnode to access
        :param field: Field name
        :return: Field value
        :raises KeyError: Field not found in vnode
        """

    @abstractmethod
    def _is_vnode(self, value):
        """ Check if a value is a vnode

        :param value: The value to check
        :return: True if it is a vnode
        """

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
        if not self.is_head(self.get_version(vnode)):
            raise ValueError("Can only set in head versions")
        if self._is_vnode(value):
            if self.get_version(vnode) != self.get_version(value):
                raise ValueError("Mismatched versions")

    @abstractmethod
    def delete(self, vnode, field):
        """ Delete a field of a vnode

        :param vnode: Vnode to delete from
        :param field: Field name
        :return: None
        :raises KeyError: Field not found in vnode
        """
        if not self.is_head(self.get_version(vnode)):
            raise ValueError("Can only delete from head versions")

    @abstractmethod
    def commit(self, head, vnodes):
        """ Create a new commit based on the given head

        In different views, this can be:
            - Split the current head in the version DAG into a commit and a
            head.
            - Change the head to a commit, create a new head on top,
            and implicitly rebind all references to head to the new head.
            - Add a copy of head as a commit to the pool of commits.

        :param head: Head to base the commit on
        :param vnodes: Vnodes which we would like references to; must be
        bound to `head`
        :return: Reference to the new commit, a list of `vnodes` rebound to it
        """
        vnodes = list(vnodes)
        assert all(self.get_version(vnode) == head for vnode in vnodes)
        return head, vnodes

    @abstractmethod
    def branch(self, commit, vnodes, *args):
        """ Create a new head based on the given commits

        Should be called as `branch(commit, vnodes[, commit2, vnodes2, ...])`
        The head's pointer machine is the disjoint union of the pointer
        machines of the originating commits.

        :param commit, commit2, ...: Commits to include in the head
        :param vnodes, vnodes2, ...: Vnodes which we would like references to;
        must be bound to corresponding commit.
        :return: Reference to the new head and a list of lists of `vnodes`
        rebound to it
        """
        # The default implementation verifies arguments and returns a list of
        #  pairs [(commit, vnodes), ...]
        commits = [commit]
        commits.extend(args[0::2])
        vnodess = [vnodes]
        vnodess.extend(args[1::2])

        if len(commits) != len(vnodess):
            raise ValueError("Invalid number of arguments, should be even")

        inputs = list(zip(commits, map(list, vnodess)))
        assert all(
            not self.is_head(cmt)
            and all(self.get_version(vn) == cmt for vn in vns)
            for cmt, vns in inputs)
        return inputs

    @abstractmethod
    def get_version(self, vnode):
        """ Get the version of a vnode

        :param vnode: Vnode to query
        :return: Version of the vnode
        """

    @abstractmethod
    def is_head(self, version):
        """ Returns whether a version is a head or a commit

        :param version: Version to query
        :return: Boolean of True if it's a head and otherwise False
        """
