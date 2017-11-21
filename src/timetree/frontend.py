from collections import OrderedDict
import contextlib
from types import MethodType

from .backend.base import BaseBackend

class Persistent(type):
    _backend = None
    _version = None

    def __init__(cls, name, bases, cdict):
        super().__init__(name, bases, cdict)

        def __new__(cls, *args, **kwargs):
            return type(cls)._get_backend().new_node(type(cls)._get_version())
        cls.__new__ = MethodType(__new__, cls)

        def __getattribute__(self, name):
            if name == '_immutables' or name in self._immutables:
                return object.__getattribute__(self, name)
            return type(cls)._get_backend().get(self, name)
        cls.__getattribute__ = MethodType(__getattribute__, cls)

        def __setattr__(self, name, value):
            if name in self._immutables:
                raise AttributeError()
            return type(cls)._get_backend().set(self, name, value)
        cls.__setattr__ = MethodType(__setattr__, cls)

        def __delattr__(self, name):
            if name in self._immutables:
                raise AttributeError()
            return type(cls)._get_backend().delete(self, name)
        cls.__delattr__ = MethodType(__delattr__, cls)

        cls._immutables = None
        cls._immutables = set(dir(cls))

    @classmethod
    def _get_backend(mcs):
        if mcs._backend is None:
            raise RuntimeError('Must be run in the context of Persistent.backend')
        return mcs._backend

    @classmethod
    def _get_version(mcs):
        if mcs._version is None:
            raise RuntimeError('Must be run in the context of Persistent.backend')
        return mcs._version

@contextlib.contextmanager
def use_backend(backend):
    if not issubclass(backend, BaseBackend):
        raise RuntimeError('not a valid Backend')
    _backend = Persistent._backend
    _version = Persistent._version
    Persistent._backend = backend()
    Persistent._version = Persistent._backend.get_base_commit()
    yield
    Persistent._backend = _backend
    Persistent._version = _version

def branch(*vnodes):
    heads = OrderedDict()
    version_indices = dict()
    vnode_indices = []
    if vnodes:
        for vnode in vnodes:
            version = Persistent._get_backend().get_version(vnode)
            if version not in heads:
                version_indices[version] = len(heads)
                heads[version] = []
            vnode_indices.append((version_indices[version], len(heads[version])))
            heads[version].append(vnode)
        args = sum(((head, vnodes) for head, vnodes in heads), ())
    else:
        args = (Persistent._version, [])
    Persistent._version, list_of_vnodes = Persistent._get_backend().branch(*args)
    results = tuple(list_of_vnodes[version_index][vnode_index] for version_index, vnode_index in vnode_indices)
    if results:
        if len(results) == 1:
            return results[0]
        return results

def commit(*vnodes):
    Persistent._version, vnodes = Persistent._get_backend().commit(Persistent._version, vnodes)
    results = tuple(vnodes)
    if results:
        if len(results) == 1:
            return results[0]
        return results
