from .base_linearized_full import BaseLinearizedDnodeBackedVnode
from .base_linearized_full import BaseLinearizedFullBackend
from .bsearch_partial import BsearchPartialDnode


class BsearchLinearizedFullVnode(BaseLinearizedDnodeBackedVnode):
    __slots__ = ()

    dnode_cls = BsearchPartialDnode


class BsearchLinearizedFullBackend(BaseLinearizedFullBackend):
    __slots__ = ()

    # Set the vnode class of the backend
    vnode_cls = BsearchLinearizedFullVnode
