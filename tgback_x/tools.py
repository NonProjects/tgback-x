from hmac import HMAC
from base64 import b32encode

__all__ = ['make_key_id']


def make_key_id(key: bytes) -> str:
    """
    This function is used for making a KeyID. Same
    Key will always result in same KeyID, though
    it's not possible to restore Key from KeyID.

    KeyID always string, starts with X, length is 32,
    consists of A-Z and 0-9. ID is case insensitive.

    E.g: XBXWFULH27FDSJ6BYXCGQTLIBBFNLWWY
    """
    keyid = HMAC(key, b'Black Sabbath', digestmod='sha256').digest()
    return 'X' + b32encode(keyid[:19]).decode()[:-1]

