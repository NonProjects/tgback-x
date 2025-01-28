from . import defaults
from . import crypto
from . import providers
from . import version
from . import protocols
from . import errors
from . import tools

from telethon import TelegramClient
from telethon.sessions import StringSession

__author__ = 'NonProjects'
__version__ = version.VERSION
__all__ = [
    'crypto',
    'providers',
    'version',
    'protocols',
    'defaults',
    'errors',
    'tools',
    'TelegramClient'
]
