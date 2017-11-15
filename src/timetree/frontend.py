import contextlib
from types import MethodType


class Persistent(type):
    _backend = None

    def __init__(cls, name, bases, cdict):
        super().__init__(name, bases, cdict)

        def __getattribute__(self, name):
            if name == '_immutables' or name in self._immutables:
                return object.__getattribute__(self, name)
            return type(cls)._get_backend().get(self, name)
        cls.__getattribute__ = MethodType(__getattribute__, None, cls)

        def __setattr__(self, name, value):
            if name in self._immutables:
                raise AttributeError()
            return type(cls)._get_backend().set(self, name, value)
        cls.__setattr__ = MethodType(__setattr__, None, cls)

        def __delattr__(self, name):
            if name in self._immutables:
                raise AttributeError()
            return type(cls)._get_backend().delete(self, name)
        cls.__delattr__ = MethodType(__delattr__, None, cls)

        cls._immutables = None
        cls._immutables = set(dir(cls))

    @classmethod
    def _get_backend(mcs):
        if mcs._backend is None:
            raise RuntimeError('Must be run in the context of Persistent.backend')
        return mcs._backend

    @classmethod
    @contextlib.contextmanager
    def backend(mcs, backend):
        _backend = mcs._backend
        mcs._backend = backend
        yield
        mcs._backend = _backend
