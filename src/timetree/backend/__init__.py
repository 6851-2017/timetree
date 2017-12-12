""" Persistence backends for timetree

These backends implement persistent pointer machines in various ways.
All backends should extend the abstract base class :py:class:`BaseBackend`,
which has more information about the persistent pointer machine model used.
Different backends may support different levels of persistence, from partial
to full to confluent persistence.
"""

from .base import BaseBackend
from .bsearch_linearized_full import BsearchLinearizedFullBackend
from .bsearch_partial import BsearchPartialBackend
from .bst_linearized_full import BSTLinearizedFullBackend
from .copy import CopyBackend
from .nop import NopBackend
from .split_linearized_full import SplitLinearizedFullBackend
from .split_partial import SplitPartialBackend

__all__ = [
    'BaseBackend',
    'BsearchLinearizedFullBackend',
    'BsearchPartialBackend',
    'BSTLinearizedFullBackend',
    'CopyBackend',
    'NopBackend',
    'SplitLinearizedFullBackend',
    'SplitPartialBackend',
]
