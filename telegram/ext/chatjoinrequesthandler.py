from telegram import Update

from .handler import Handler
from .utils.types import CCT


class ChatJoinRequestHandler(Handler[Update, CCT]):
        __slots__ = ()

    def check_update(self, update: object) -> bool:
        return isinstance(update, Update) and bool(update.chat_join_request)
