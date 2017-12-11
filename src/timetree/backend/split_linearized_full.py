from weakref import WeakSet

from .base_dnode import BaseDnode
from .base_dnode import BaseDnodeBackedVnode
from .base_linearized_full import BaseLinearizedFullBackend


class Mod:
    __slots__ = ('value', 'source', 'field', 'start_version', 'end_version', '__weakref__',)

    def __init__(self, value, source, field, start_version, end_version):
        self.value = value
        self.source = source
        self.field = field
        self.start_version = start_version
        self.end_version = end_version
        assert start_version < end_version


class SplitLinearizedFullDnode(BaseDnode):
    __slots__ = ('start_version', 'end_version', 'mods_dict', 'backrefs', 'vnodes',)

    _deleted_marker = object()

    def __init__(self, backend):
        super().__init__(backend)
        self.start_version = backend.v_0
        self.end_version = backend.v_inf
        self.mods_dict = {}
        self.backrefs = WeakSet()
        self.vnodes = WeakSet()

    def get(self, field, version_num):
        if not self.start_version <= version_num < self.end_version:
            raise ValueError('version_num was invalid for this dnode')

        if field not in self.mods_dict:
            raise KeyError("Field doesn't exist")

        mods = self.mods_dict[field]

        assert len(mods) >= 1

        assert mods[0].start_version == self.start_version
        assert mods[-1].end_version == self.end_version

        for ind, mod in enumerate(mods):
            if mod.start_version <= version_num < mod.end_version:
                break
        else:
            assert False

        if mod.value == self._deleted_marker:
            raise KeyError("Field doesn't exist")
        return mod.value

    def set(self, field, value, version_num):
        if not self.start_version <= version_num < self.end_version:
            raise ValueError('version_num was invalid for this dnode')

        if field not in self.mods_dict:
            self.mods_dict[field] = [
                Mod(
                    self._deleted_marker,
                    self,
                    field,
                    self.start_version,
                    self.end_version,
                )
            ]

        mods = self.mods_dict[field]

        assert len(mods) >= 1

        assert mods[0].start_version == self.start_version
        assert mods[-1].end_version == self.end_version

        for ind, old_mod in enumerate(mods):
            if old_mod.start_version <= version_num < old_mod.end_version:
                break
        else:
            assert False

        assert old_mod.start_version <= version_num < old_mod.end_version

        assert old_mod.source == self
        assert old_mod.field == field

        st_ver = old_mod.start_version
        en_ver = old_mod.end_version

        split_set = {self}

        # Helper methods to add or remove existing backrefs to dnodes
        def del_backref(mod):
            if isinstance(mod.value, SplitLinearizedFullDnode):
                mod.value.backrefs.remove(mod)

        def add_backref(mod):
            if isinstance(mod.value, SplitLinearizedFullDnode):
                mod.value.backrefs.add(mod)
                split_set.add(mod.value)

        if st_ver == version_num and en_ver == version_num.next:

            # We actually don't need to split ourselves
            split_set.remove(self)

            del_backref(old_mod)
            old_mod.value = value
            add_backref(old_mod)
        elif st_ver == version_num:
            old_mod.start_version = version_num.next

            new_mod = Mod(
                value,
                self,
                field,
                version_num,
                version_num.next,
            )

            mods.insert(ind, new_mod)
            add_backref(new_mod)
        else:
            old_mod.end_version = version_num

            new_mod = Mod(
                value,
                self,
                field,
                version_num,
                version_num.next,
            )

            mods.insert(ind+1, new_mod)
            add_backref(new_mod)

            if en_ver > version_num.next:
                tail_mod = Mod(
                    old_mod.value,
                    self,
                    field,
                    version_num.next,
                    en_ver,
                )
                mods.insert(ind+2, tail_mod)
                add_backref(tail_mod)

        while split_set:
            cur = split_set.pop()
            cur._split(split_set)

    def _split(self, split_set):
        # Decide if we should split
        num_fields = len(self.mods_dict)
        num_mods = sum(map(len, self.mods_dict.values()))
        if num_mods <= 20:
            return
        if num_mods <= 5 * num_fields:
            return

        split_points = {self.start_version, self.end_version}.union(
            mod.start_version for mods in self.mods_dict.values() for mod in mods
        ).union(
            mod.start_version for mod in self.backrefs
        )
        split_points = sorted(split_points)
        assert len(split_points) >= 2
        if len(split_points) == 2:
            # We only have the start and the end
            return

        split_point = split_points[len(split_points) // 2]
        assert self.start_version < split_point < self.end_version

        new_dnode = SplitLinearizedFullDnode(backend=self.backend)

        new_dnode.end_version = self.end_version
        new_dnode.start_version = split_point
        self.end_version = split_point

        for field in self.mods_dict:
            mods = self.mods_dict[field]
            for ind, split_mod in enumerate(mods):
                if split_mod.start_version <= split_point < split_mod.end_version:
                    break
            else:
                assert False

            if split_mod.start_version < split_point:
                new_mod = Mod(
                    split_mod.value,
                    self,
                    field,
                    split_point,
                    split_mod.end_version,
                )
                split_mod.end_version = split_point

                mods.insert(ind+1, new_mod)
                if isinstance(new_mod.value, SplitLinearizedFullDnode):
                    new_mod.value.backrefs.add(new_mod)
                    split_set.add(new_mod.value)

                # Update split_mod for consistency
                split_mod = new_mod
                ind += 1

            new_dnode.mods_dict[field] = mods[ind:]
            self.mods_dict[field] = mods[:ind]

            for mod in new_dnode.mods_dict[field]:
                mod.source = new_dnode

        backrefs = self.backrefs
        self.backrefs = WeakSet()

        for mod in backrefs:
            assert mod.value == self
            if mod.end_version <= split_point:
                self.backrefs.add(mod)
            elif mod.start_version >= split_point:
                mod.value = new_dnode
                new_dnode.backrefs.add(mod)
            else:
                new_mod = Mod(
                    new_dnode,
                    mod.source,
                    mod.field,
                    split_point,
                    mod.end_version,
                )
                mod.end_version = split_point

                src_mods = mod.source.mods_dict[mod.field]
                ind = src_mods.index(mod)
                src_mods.insert(ind + 1, new_mod)
                split_set.add(mod.source)

                self.backrefs.add(mod)
                new_dnode.backrefs.add(new_mod)

        vnodes = self.vnodes
        self.vnodes = WeakSet()

        for vnode in vnodes:
            assert vnode.dnode == self
            assert self.start_version <= vnode.version.version_num < new_dnode.end_version
            if vnode.version.version_num < split_point:
                self.vnodes.add(vnode)
            else:
                vnode.dnode = new_dnode
                new_dnode.vnodes.add(vnode)

        # Split again if necessary
        self._split(split_set)
        new_dnode._split(split_set)

    def delete(self, field, version_num):
        if not self.start_version <= version_num < self.end_version:
            raise ValueError('version_num was invalid for this dnode')
        self.set(field, self._deleted_marker, version_num)


class SplitLinearizedFullVnode(BaseDnodeBackedVnode):
    __slots__ = ('__weakref__')

    dnode_cls = SplitLinearizedFullDnode

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dnode.vnodes.add(self)


class SplitLinearizedFullBackend(BaseLinearizedFullBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = SplitLinearizedFullVnode
