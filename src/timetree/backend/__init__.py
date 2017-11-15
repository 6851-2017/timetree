""" Persistence backends for timetree

These backends implement persistent pointer machines in various ways.
All backends should extend the abstract base class :py:class:`BaseBackend`,
which has more information about the persistent pointer machine model used.
Different backends may support different levels of persistence, from partial
to full to confluent persistence.
"""

from .base import BaseBackend

__all__ = [
    'BaseBackend',
]
