import contextlib
import types
from functools import wraps

from .backend.base import BaseVersion

__all__ = ['use_version', 'make_persistent', 'branch', 'commit']

global_version = None


@contextlib.contextmanager
def use_version(version):
    global global_version

    if isinstance(version, BaseVersion):
        raise TypeError('not a valid Version')

    old_version = global_version
    global_version = version

    yield

    global_version = old_version


# Marker class
class TimetreeProxy:
    __slots__ = ()


def make_persistent(klass):
    class KlassTimetreeProxy(klass, TimetreeProxy):
        __slots__ = ('_timetree_vnode',)

        def __new__(cls, *args,
                    timetree_vnode=None,
                    timetree_version=None,
                    timetree_backend=None,
                    **kwargs):
            global global_version

            if \
                    timetree_vnode is not None or\
                    timetree_version is not None or\
                    timetree_backend is not None or\
                    global_version is not None:
                return super().__new__(cls, *args, **kwargs)

            return klass(*args, **kwargs)

        def __init__(self, *args,
                     timetree_vnode=None,
                     timetree_version=None,
                     timetree_backend=None,
                     **kwargs):
            if timetree_vnode is not None:
                object.__setattr__(self, '_timetree_vnode', timetree_vnode)
                return

            if timetree_version is None:
                # Get the version
                if timetree_backend is not None:
                    timetree_version = timetree_backend.branch()
                elif global_version is not None:
                    timetree_version = global_version
                else:
                    assert False, "No version to use; __new__ should check that"

            vnode = timetree_version.new_node()
            object.__setattr__(self, '_timetree_vnode', vnode)
            vnode.set('_timetree_proxy_class', self.__class__)

            super().__init__(*args, **kwargs)

        def __getattribute__(self, name):
            vnode = object.__getattribute__(self, '_timetree_vnode')
            try:
                result = vnode.get(name)
                if vnode.backend.is_vnode(result):
                    result = get_proxy(result)
                return result
            except KeyError:
                result = super().__getattribute__(name)

                # Wrap instance methods
                if isinstance(result, types.MethodType) \
                        and result.__self__ is self:
                    version = vnode.version

                    @wraps(result)
                    def wrapped_result():
                        with use_version(version):
                            return result()

                    result = wrapped_result
                return result

        def __setattr__(self, name, value):
            vnode = object.__getattribute__(self, '_timetree_vnode')

            # Handle data descriptors, which get priority
            for cls in self.__class__.__mro__:
                if name in cls.__dict__:
                    obj = cls.__dict__[name]
                    if hasattr(obj, '__set__'):
                        return obj.__set__(self, value)

            if isinstance(value, TimetreeProxy):
                o_vnode = object.__getattribute__(value, '_timetree_vnode')
                if vnode.backend.is_vnode(o_vnode):
                    value = o_vnode

            return vnode.set(name, value)

        def __delattr__(self, name):
            vnode = object.__getattribute__(self, '_timetree_vnode')

            # Handle data descriptors, which get priority
            for cls in self.__class__.__mro__:
                if name in cls.__dict__:
                    obj = cls.__dict__[name]
                    if hasattr(obj, '__delete__'):
                        return obj.__delete__(self)

            return vnode.delete(name)

    return KlassTimetreeProxy


def get_proxy(vnode):
    return vnode.get('_timetree_proxy_class')(_timetree_vnode=vnode)


def get_vnode(proxy):
    if not isinstance(proxy, TimetreeProxy):
        raise TypeError("proxy is not a TimetreeProxy")
    return object.__getattribute__(proxy, '_timetree_vnode')


def get_version(proxy):
    return get_vnode(proxy).version


def get_backend(proxy):
    return get_vnode(proxy).backend


def branch(*args):
    """ Creates a new branch from a list of proxy objects

    Takes either a single iterable, or many objects as arguments.

    If no arguments are given, creates a new branch and return the version
    object.

    If a single proxy object is given as the argument, return a new proxy to
    the object.

    If an iterable is given, or at least two arguments are given, return a
    tuple of proxies to the new vnodes.
    """
    return _create_version(args, is_branch=True)


def commit(*args):
    """ Creates a new commit from a list of proxy objects

    Takes either a single iterable, or many objects as arguments.

    If no arguments are given, creates a new commit and return the version
    object.

    If a single proxy object is given as the argument, return a new proxy to
    the object.

    If an iterable is given, or at least two arguments are given, return a
    tuple of proxies to the new vnodes.
    """
    return _create_version(args, is_commit=True)


def _create_version(args, *, is_branch=False, is_commit=False):
    """ Internal implementation of branch and commit """
    assert int(is_branch) + int(is_commit) == 1,\
        "Exactly one of is_branch and is_commit should be true"

    backend = get_backend(args[0]) if args else global_version.backend
    make_version = backend.branch if is_branch else backend.commit

    if not args:
        return make_version()

    if len(args) == 1 and not isinstance(args[0], TimetreeProxy):
        # We were given an iterator
        is_iterator = True
        if not hasattr(args[0], '__iter__'):
            raise TypeError("Only argument was neither a TimetreeProxy nor an iterator")
        args = tuple(args[0])
    else:
        is_iterator = False

    _, vnodes = make_version(get_vnode(proxy) for proxy in args)
    vnodes = (get_proxy(vnode) for vnode in vnodes)
    if is_iterator:
        return list(vnodes)
    elif len(args) == 1:
        return next(vnodes)
    else:
        return tuple(vnodes)
