from enum import IntEnum
from pathlib import Path
try:
    from sys import _MEIPASS
except ImportError:
    _MEIPASS = None

__all__ = ['Scrypt', 'ABSPATH']


ABSPATH: Path = Path(_MEIPASS) if _MEIPASS is not None \
    else Path(__file__).parent

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/131.0.0.0 Safari/537.36'
)
class Scrypt(IntEnum):
    SALT:  int=0x5261696E626F77202D205374617267617A6572207C20C2E467EF2FBBC8ABB46B
    DKLEN: int=32
    N:     int=2**20
    R:     int=8
    P:     int=1

