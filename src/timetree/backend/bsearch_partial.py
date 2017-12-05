from .base_dnode import BaseDnodeBackedVnode
from .base_dnode import BsearchDnode
from .base_partial import BasePartialBackend


class BsearchPartialVnode(BaseDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = BsearchDnode


class BsearchPartialBackend(BasePartialBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = BsearchPartialVnode
