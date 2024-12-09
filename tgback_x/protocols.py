from json import loads, dumps
from hmac import HMAC

from abc import ABC, abstractmethod
from base64 import urlsafe_b64encode, urlsafe_b64decode

from .errors import ProtocolNotInstalled
from .crypto import get_rnd_bytes, Key, AES, KeyAES

__all__ = [
    'Protocol', 'JSON_AES_CBC_UB64',
    'Universal', 'PROTOCOL_MAP'
]

class Protocol(ABC):
    """
    Protocol abstract class is a class that is used to
    make encryption protocols. The default proposed one
    is JSON_AES_CBC_UB64(), although your implementation
    may have their own to use in Provider.
    """
    @abstractmethod
    def __init__(self, key: Key):
        """key is an encryption / decryption key."""
        raise NotImplementedError

    @abstractmethod
    def capsulate(self, **kwargs) -> str:
        """
        capsulate() is a method that should accept any
        amount of kwargs, pack them in bytes, encrypt
        and then encode with some function to convert
        it to (and return as) string (e.g base64).

        You're recommended not to use encryption Key
        directly, rather Salt it with some random
        bytes and include Salt in a resulted data.

        !! ATTENTION !!

        If you wish to implement your own Protocol,
        your capsulate() method SHOULD return data
        encoded AND PREFIXED with your Protocol
        (class) name plus underscore, for example,
        f'{self.__class__.__name__}_{encoded_data}'.

        ALSO, your Protocol class should be added
        to PROTOCOL_MAP dictionary (in this module),
        either directly here in code OR in YOUR
        side module (with PROTOCOL_MAP import)

        This is REQUIRED for Universal() to work
        correctly.

        !! --------- !!
        """
        raise NotImplementedError

    @abstractmethod
    def extract(self, data: str) -> dict:
        """
        extract() is a method that should accept capsulated
        data, extract it, convert to Python dict and return
        """
        raise NotImplementedError

class JSON_AES_CBC_UB64(Protocol):
    """
    JSON_AES_CBC_UB64 is a Protocol that is using JSON to
    pack data, AES-CBC-256, to encrypt it, HMAC-SHA256 as
    MAC and Urlsafe Base64 to encode.
    """
    def __init__(self, key: KeyAES):
        self._key = key

    @staticmethod
    def make_salted_key(key: KeyAES, salt: bytes) -> KeyAES:
        # We don't encrypt directly with self._key, instead,
        # we Salt it and produce encryption Key with HMAC
        sk = HMAC(key.raw, salt, digestmod='sha256').digest()
        return KeyAES(sk)

    def capsulate(self, **kwargs) -> str:
        """
        capsulate() will pack, encrypt and encode all of
        specified kwargs. Keyword arguments can be any
        type that JSON can support. Bytes will be encoded
        additionally and decoded on extract(). Take a note
        that it's pretty dumb, so doesn't support containers
        with bytes, e.g [b''] or (b'',) is error.
        """
        k_decode = []
        for k,v in kwargs.items():
            if isinstance(v, bytes): # JSON can't store raw bytes
                kwargs[k] = urlsafe_b64encode(v).decode()
                k_decode.append(k) # Will decode this keys on extract

        kwargs['k_deco'] = k_decode # base64 encoded keys
        kwargs = dumps(kwargs).encode()

        salt = get_rnd_bytes(32)
        ekey = self.make_salted_key(self._key, salt)

        kwargs = salt + AES.encrypt(ekey, kwargs)
        kwargs = urlsafe_b64encode(kwargs).decode()
        proto_name = self.__class__.__name__

        return f'{proto_name}_{kwargs}'

    def extract(self, data: str) -> dict:
        """extract() decrypts and unpacks capsulated data."""
        # Remove Proto prefix (if in string)
        proto_name = self.__class__.__name__
        data = data.replace(f'{proto_name}_','')

        data = urlsafe_b64decode(data)
        data, salt = data[32:], data[:32]

        ekey = self.make_salted_key(self._key, salt)
        data = loads(AES.decrypt(ekey, data))

        for k in data['k_deco']:
            data[k] = urlsafe_b64decode(data[k])
        data.pop('k_deco')
        return data

class Universal(Protocol):
    """
    Universal is a dynamic, high-level Protocol that
    can automatically use the encryption scheme that
    was specified in capsulated() data result.

    With Universal() front app devs don't need to
    parse or interact with the capsulated data to
    select Protocol to use.
    """
    def __init__(self, key: Key):
        self._raw_key = key.raw
        self._key = None
        self._protocol = None

    def __check_protocol(self):
        if not self._protocol:
            raise ValueError(
                'We don\'t know which Protocol you want to use. '
                'Use .extract() firstly or .set_protocol()'
            )
    def set_protocol(self, protocol: str):
        """Set Universal() protocol (must be in PROTOCOL_MAP)"""
        try:
            pmap = PROTOCOL_MAP[protocol]
        except IndexError as e:
            raise ProtocolNotInstalled(ProtocolNotInstalled.__doc__.format(protocol)) from e

        self._key = pmap['k'](self._raw_key)
        self._protocol = pmap['c'](self._key)

    def capsulate(self, **kwargs) -> str:
        """Will use underlying <Protocol>.capsulate()"""
        self.__check_protocol()
        return self._protocol.capsulate(**kwargs)

    def extract(self, data: str, **kwargs) -> dict:
        """Will use underlying <Protocol>.extract()"""
        if not self._protocol:
            self.set_protocol(data.split('_',1)[0])
        return self._protocol.extract(data=data, **kwargs)


# Maps are used by the Universal classes. If you
# plan to develop your own Protocol, then don't
# forget to import PROTOCOL_MAP and add your
# Protocol class here (dict key is a class name)
PROTOCOL_MAP = {
    'JSON_AES_CBC_UB64': {
        'c': JSON_AES_CBC_UB64, # [c]lass
        'k': KeyAES # [k]ey
    },
}
