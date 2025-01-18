from re import findall as re_findall
from abc import ABC, abstractmethod

from datetime import datetime
from urllib.request import Request, urlopen

from telethon.tl.functions.channels import (
    CreateChannelRequest, DeleteChannelRequest,
    UpdateUsernameRequest, EditTitleRequest
)
from telethon.errors import (
    ChannelsAdminPublicTooMuchError,
    ChatAdminRequiredError,
    UsernameNotOccupiedError
)
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, MessageService

from .errors import (
    NoDataByKeyID, TooManyPublicLinks, OccupiedKeyID,
    NotEnoughRights, SessionDisconnected
)
from .protocols import JSON_AES_CBC_UB64
from .defaults import USER_AGENT
from .version import VERSION
from .crypto import Key

__all__ = ['Provider', 'TelegramChannel', 'PROVIDER_MAP']


class Provider(ABC):
    """
    Abstract Provider is a class that is used to store
    an encrypted backup. You will need to inherit this
    class if you want to implement your own backend. See
    implementation of TelegramChannel provider as ref.
    """
    @abstractmethod
    def store(self, key: Key, client: TelegramClient) -> str:
        """
        This method should take User key and client (both
        provided by the front App), make a KeyID from key
        and store client data (session, etc) in an encrypted
        by Protocol (i.e JSON_AES_CBC_UB64) form on some
        backend. Encrypted data should be linked to KeyID.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, key: Key, raw_data=None) -> TelegramClient:
        """
        This method should return stored client object by key.
        Key -> KeyID -> Get data by KeyID -> decrypt data with
        Key using Protocol -> Restore and return client.

        You should implement a support for Raw data. Raw data
        is an encrypted and encoded backup data produced by
        Protocol that you directly store on Provider's side, so
        instead of obtaining it through key, you should be able
        to get it from user.
        """
        raise NotImplementedError

    @abstractmethod
    def destroy(self, key: Key) -> None:
        """
        This method SHOULD disconnect Telegram client
        session and remove encrypted by Protocol backup
        from the Provider server (if possible).
        """
        raise NotImplementedError

class TelegramChannel(Provider):
    """
    TelegramChannel provider is a default TGBACK-X
    provider that uses Telegram channel as backend
    and JSON_AES_CBC_UB64 as encryption Protocol.

    We store encrypted data in a public channel,
    public link of which is a KeyID. As Telegram
    allows preview of Public Channels right in a
    browser without login, we parse the page and
    obtain the backup.
    """
    def __init__(self, user_agent: str=USER_AGENT):
        self._user_agent = user_agent

    def _get_data(self, keyid: str) -> str:
        """
        Ask for a Channel preview page data, parse it
        and return encrypted data (if Channel exists).
        """
        request = Request(
            url = f'https://t.me/s/{keyid}',
            headers = {'User-Agent': self._user_agent}
        )
        page = urlopen(request).read()
        # I believe that RegularExp search on page source
        # in our case is more stable than using, e.g, bs4,
        # as Telegram team can change front at any time.
        data = re_findall(rb'(\+T\+.*?\+T\+)', page)

        if not data:
            raise NoDataByKeyID(NoDataByKeyID.__doc__)
        return data[-1].strip(b'+T+<br/>').decode()

    def set_user_agent(self, ua: str) -> None:
        """You can change User Agent for _get_data()."""
        self._user_agent = ua

    def store(self, key: Key, client: TelegramClient) -> Channel:
        """
        This method will store your client session and
        other metadata in an encrypted by JSON_AES_CBC_UB64
        protocol form in a Telegram Channel.

        The output from the JSON_AES_CBC_UB64.capsulate()
        will be prefixed and suffixed with "+T+\n" and
        "\n+T+" (i.e f"+T+\n{data}\n+T+") to make parsing
        in .get() easier.
        """
        date = datetime.now()

        data_d = {
            'session': client.session.save(),
            'api_id': client.api_id,
            'api_hash': client.api_hash,
            'created_at': date.timestamp(),
            'version': VERSION
        }
        p = JSON_AES_CBC_UB64(key)
        data_d = p.capsulate(**data_d)
        try:
            channel = client.get_input_entity(key.id)
        except (ValueError, UsernameNotOccupiedError):
            channel = client(
                CreateChannelRequest(
                    title = f'TgbX ({date.ctime()})',
                    about = f'Made with TGBACK-X v{VERSION}',
                    megagroup = False
                )
            ).chats[0]
            try:
                client(
                    UpdateUsernameRequest(
                        channel = channel,
                        username = key.id
                    )
                )
            except ChannelsAdminPublicTooMuchError as e:
                raise TooManyPublicLinks(TooManyPublicLinks.__doc__) from e
        try:
            client.send_message(channel, f'+T+\n{data_d}\n+T+')
        except ChatAdminRequiredError as e:
            raise OccupiedKeyID(OccupiedKeyID.__doc__) from e

        return channel

    def get(self, key: Key, raw_data=None) -> TelegramClient:
        """
        Will return a TelegramClient object if key is
        linked to an active Telegram session X-Backup.

        You can specify Backup data directly in raw_data
        if it's impossible to fetch from the Provider.
        """
        if raw_data:
            data = raw_data.replace('+T+', '') # If in data.
        else:
            data = self._get_data(key.id)

        p = JSON_AES_CBC_UB64(key)
        data = p.extract(data)

        client = TelegramClient(
            session = StringSession(data['session']),
            api_id = data['api_id'],
            api_hash = data['api_hash']
        )
        client.connect()

        if client.get_me() is None:
            raise SessionDisconnected(SessionDisconnected.__doc__)

        date_str = datetime.now().ctime()
        backup_channel = client.get_entity(key.id)
        client(EditTitleRequest(backup_channel, f'TgbX ({date_str})'))

        service_msg = next(client.iter_messages(backup_channel))
        if isinstance(service_msg, MessageService):
            # MessageService is, i.e, "Channel name changed to X"
            client.delete_messages(backup_channel, service_msg.id)
        return client

    def destroy(self, key: Key) -> None:
        """
        This method will disconnect Telegram client
        session and remove Channel where encrypted
        backup is stored (if possible).
        """
        client = self.get(key)
        try:
            channel = client.get_input_entity(key.id)
        except (ValueError, UsernameNotOccupiedError) as e:
            raise NoDataByKeyID(NoDataByKeyID.__doc__) from e
        try:
            not_enough_rights = None
            client(DeleteChannelRequest(channel))
        except ChatAdminRequiredError as e:
            not_enough_rights = e
        try:
            # We will always try to force disconnect a session even if
            # we don't have rights to modify a Backup channel. This
            # may be important: if someone else will get into User
            # account through backup, we would WANT to provide them
            # at least ability to destroy this session for all.
            client.log_out()
        except Exception as e:
            raise SessionDisconnected(
                "Impossible to disconnect session. Either it was "
                "disconnected prior or there is some problem. Try "
                "again or disconnect manually in Telegram settings "
                "-> Devices.") from e

        if not_enough_rights:
            raise NotEnoughRights(
                "You don't have enough rights to be able "
                "to remove storage Channel.") from not_enough_rights


# Maps are used by the Universal classes. If you
# plan to develop your own Provider, then don't
# forget to import PROVIDER_MAP and add your
# Provider class here (dict key is a class name)
PROVIDER_MAP = {
    'TelegramChannel': TelegramChannel
}
