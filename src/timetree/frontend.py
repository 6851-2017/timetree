import contextlib

class Persistent(type):
    _backend = None

    def __init__(cls, name, bases, cdict):
        super().__init__(name, bases, cdict)

        def __getattribute__(self, name):
            if name == '_immutables' or name in self._immutables:
                return object.__getattribute__(self, name)
            return cls._get_backend().get(self, name)
        cls.__getattribute__ = __getattribute__

        def __setattr__(self, name, value):
            if name in self._immutables:
                raise AttributeError()
            return cls._get_backend().set(self, name, value)
        cls.__setattr__ = __setattr__

        def __delattr__(self, name):
            if name in self._immutables:
                raise AttributeError()
            return cls._get_backend().delete(self, name)
        cls.__delattr__ = __delattr__

        cls._immutables = None
        cls._immutables = set(dir(cls))

    @classmethod
    def _get_backend(cls):
        if cls._backend is None:
            raise RuntimeError('Must be run in the context of Persistent.backend')
        return cls._backend

    @classmethod
    @contextlib.contextmanager
    def backend(cls, backend):
        _backend = cls._backend
        cls._backend = backend
        yield
        cls._backend = _backend
