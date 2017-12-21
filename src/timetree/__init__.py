__version__ = '0.1.1'


from . import backend
from . import frontend
from .frontend import branch
from .frontend import commit
from .frontend import get_proxy_backend
from .frontend import get_proxy_version
from .frontend import make_persistent
from .frontend import use_backend
from .frontend import use_proxy_version
from .frontend import use_version

__all__ = [
    'backend',
    'frontend',
    'make_persistent',
    'get_proxy_backend',
    'get_proxy_version',
    'use_version',
    'use_backend',
    'use_proxy_version',
    'commit',
    'branch',
]
