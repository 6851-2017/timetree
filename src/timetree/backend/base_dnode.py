from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict
from collections import namedtuple

from .base_partial import BaseCopyableVnode

Mod = namedtuple('Mod', ['version_num', 'value'])


class BaseDnode(metaclass=ABCMeta):
    __slots__ = ()

    @abstractmethod
    def get(self, field, version_num):
        pass

    @abstractmethod
    def set(self, field, value, version_num):
        pass

    @abstractmethod
    def delete(self, field, version_num):
        pass


class BsearchDnode(BaseDnode):
    __slots__ = ('mods_dict',)

    _deleted_marker = object()

    def __init__(self):
        self.mods_dict = defaultdict(list)

    def get(self, field, version_num):
        if field not in self.mods_dict:
            raise KeyError('Never created')
        mods = self.mods_dict[field]

        assert mods, "Mods shouldn't be empty if it's in the dict"

        # OPTIMIZATION: Fast-path for present-time queries
        if mods[-1].version_num <= version_num:
            result = mods[-1].value
        else:
            # Binary search to find the last mod <= self.version_num
            mi = -1
            ma = len(mods)
            while ma - mi > 1:
                md = (mi + ma) // 2
                if mods[md].version_num <= version_num:
                    mi = md
                else:
                    ma = md

            if mi == -1:
                raise KeyError('Not created yet')

            result = mods[mi].value

        if result is self._deleted_marker:
            raise KeyError('Field deleted')

        return result

    def set(self, field, value, version_num):
        mods = self.mods_dict[field]
        if not mods or mods[-1].version_num <= version_num:
            mods.append(Mod(version_num, value))
        else:
            mi = -1
            ma = len(mods)
            while ma - mi > 1:
                md = (mi + ma) // 2
                if mods[md].version_num <= version_num:
                    mi = md
                else:
                    ma = md
            mods.insert(ma, Mod(version_num, value))

    def delete(self, field, version_num):
        self.set(field, self._deleted_marker, version_num)


class BaseDnodeBackedVnode(BaseCopyableVnode):
    __slots__ = ('dnode', )

    dnode_cls = BaseDnode  # Illegal

    def __init__(self, version, *, dnode=None):
        super().__init__(version)

        if dnode is not None:
            # Restore an old vnode
            self.dnode = dnode
            return

        self.dnode = self.dnode_cls()

    def get(self, field):
        super().get(field)
        result = self.dnode.get(field, self.version.version_num)
        if isinstance(result, self.dnode_cls):
            result = self.__class__(self.version, dnode=result)
        return result

    def set(self, field, value):
        super().set(field, value)
        if self.backend.is_vnode(value):
            value = value.dnode
        self.dnode.set(field, value, self.version.version_num)

    def delete(self, field):
        super().delete(field)
        self.dnode.delete(field, self.version.version_num)

    def copy(self, version):
        return self.__class__(version, dnode=self.dnode)

    def __eq__(self, other):
        return (self.version, self.dnode) == (other.version, other.dnode)

    def __hash__(self):
        return hash((self.version, self.dnode))
