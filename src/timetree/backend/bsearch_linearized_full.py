from .base_dnode import BsearchDnode
from .base_linearized_full import BaseLinearizedDnodeBackedVnode
from .base_linearized_full import BaseLinearizedFullBackend


class BsearchLinearizedFullVnode(BaseLinearizedDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = BsearchDnode


class BsearchLinearizedFullBackend(BaseLinearizedFullBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = BsearchLinearizedFullVnode
