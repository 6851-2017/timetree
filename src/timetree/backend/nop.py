from .base import BaseBackend
from .base import BaseVersion
from .base import BaseVnode


class NopBackend(BaseBackend):
    """ Timetree backend which doesn't support any persistence (no commits,
    only one head)
    """

    __slots__ = ('head',)

    def __init__(self):
        super().__init__()
        self.head = None

    def commit(self, vnodes=None):
        """Commit is an illegal operation"""
        vnodes = super().commit(vnodes)
        raise NotImplementedError

    def branch(self, vnodes=None):
        """ Branch only once from the empty commit """
        vnodes = super().branch(vnodes)

        if vnodes:
            raise ValueError('NopBackend does not support branching from a commit')
        if self.head is not None:
            raise ValueError('NopBackend only supports one head')
        self.head = NopVersion(self)

        return self.head, []


class NopVersion(BaseVersion):
    """ Only exists as a head """
    __slots__ = ('backend', 'is_head')

    def __init__(self, backend):
        super().__init__()
        self.backend = backend
        self.is_head = True

    def new_node(self):
        super().new_node()
        return NopVnode(self)


class NopVnode(BaseVnode):
    __slots__ = ('version', 'values')

    def __init__(self, version):
        super().__init__()
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
