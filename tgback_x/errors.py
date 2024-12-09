
class Tgback_X_Error(Exception):
    """Base Tgback-X exception"""

class ProtocolNotInstalled(Tgback_X_Error):
    """
    The Protocol '{0}' is not installed in your build of TGBACK-X
    or is incorrect. Please refer to documentation of your build.
    """
class NoDataByKeyID(Tgback_X_Error):
    """
    No data found by specified KeyID. Typically it means
    that you typed incorrect Passphrase. Try again.
    """
class OccupiedKeyID(Tgback_X_Error):
    """
    You can not make backup with a current Passphrase.
    Please generate random one and try again.
    """
class TooManyPublicLinks(Tgback_X_Error):
    """
    TelegramChannel provider require at least one free public
    username on account, but you reached a limit. Consider to
    clear username/link from one of your Channel or Group and
    try again. Can not continue for now.
    """
class SessionDisconnected(Tgback_X_Error):
    """
    Backup session was disconnected either by Owner or Telegram.
    """
class NotEnoughRights(Tgback_X_Error):
    """
    You don't have enough rights for this action
    """
