from hashlib import scrypt
from os import urandom
from hmac import HMAC

from pyaes import AESModeOfOperationCBC, Encrypter, Decrypter

from .defaults import Scrypt
from .tools import make_key_id

__all__ = [
    'Key', 'KeyAES', 'AES', 'make_scrypt_key', 
    'get_rnd_bytes', 'KEY_MAP'
]

class Key:
    """
    Key is a class that wraps keys as bytes. You
    can inherit it and make your own Key, with
    _REQ_LENGTH specified to desired.
    """
    _REQ_LENGTH = 0 # Required bytelength for your Key

    def __init__(self, key: bytes):
        if self._REQ_LENGTH and len(key) != self._REQ_LENGTH:
            raise ValueError(f'Key length must be {self._REQ_LENGTH}')
        self._key = key

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(key={self._key})'

    def __str__(self) -> str:
        return f'<{self.__class__.__name__} @ {self.hex[:12]}...>'

    def __add__(self, other: bytes) -> bytes:
        return self._key + other

    @property
    def raw(self) -> bytes:
        """Returns raw Key as bytes"""
        return self._key

    @property
    def hex(self) -> str:
        """Returns Key as hex"""
        return self._key.hex()

    @property
    def id(self) -> str:
        """Returns unique Key ID"""
        return make_key_id(self._key)

    @classmethod
    def generate(cls):
        """Generate and return random Key"""
        return cls(get_rnd_bytes(cls._REQ_LENGTH))

class KeyAES(Key):
    _REQ_LENGTH = 32

    def __init__(self, key: bytes):
        super().__init__(key)

class AES:
    """
    A basic, stateless implementation of AES-CBC-256.
    All data will be encrypted/padded OR decrypted/
    unpadded in one call. First 16 bytes of encrypted
    data is always IV. This AES implementation will
    also add HMAC-SHA256 over IV + Encrypted Data
    and append it to Encrypted Data (last 32 bytes).
    """
    @staticmethod    
    def encrypt(key: KeyAES, data: bytes) -> bytes:
        """
        Arguments:
            key (``KeyAES``):
                32 byte encryption key

            data (``bytes``):
                Data to encrypt.
        """
        iv = get_rnd_bytes(16)
        cbc256 = Encrypter(AESModeOfOperationCBC(key=key.raw, iv=iv))
        hmackey = HMAC(key.raw, b'Holy Diver', digestmod='sha256')

        data = iv + cbc256.feed(data) + cbc256.feed()
        hmac = HMAC(hmackey.digest(), data, digestmod='sha256')
        return data + hmac.digest()
    
    @staticmethod
    def decrypt(key: KeyAES, data: bytes) -> bytes:
        """
        Arguments:
            key (``Key``):
                32 byte decryption key

            data (``bytes``):
                Data to decrypt.
        """
        hmac, data = data[-32:], data[:-32]
        hmackey = HMAC(key.raw, b'Holy Diver', digestmod='sha256')

        if HMAC(hmackey.digest(), data, digestmod='sha256').digest() != hmac:
            raise ValueError('HMAC differ!! Aborting decryption!')

        iv, data = data[:16], data[16:]
        cbc256 = Decrypter(AESModeOfOperationCBC(key=key.raw, iv=iv))
        return cbc256.feed(data) + cbc256.feed()

def make_scrypt_key(
        password: bytes,
        *,
        salt: int=Scrypt.SALT.value,
        n: int=Scrypt.N.value,
        r: int=Scrypt.R.value,
        p: int=Scrypt.P.value,
        dklen: int=Scrypt.DKLEN.value) -> bytes:
    """
    Will use 1GB of RAM by default.
    memory = 128 * r * (n + p + 2)
    """
    if isinstance(salt, int):
        bit_length = ((salt.bit_length() + 8) // 8)
        length = (bit_length * 8 ) // 8

        salt = int.to_bytes(salt, length, 'big')

    m = 128 * r * (n + p + 2)
    return scrypt(
        password, n=n, r=r, dklen=dklen,
        p=p, salt=salt, maxmem=m
    )

def get_rnd_bytes(size: int) -> bytes:
    """Returns urandom(size)"""
    return urandom(size)

# You are recommended to add your custom Keys
# here. Maybe it will be useful in future.
KEY_MAP = {
    'KeyAES': KeyAES
}
