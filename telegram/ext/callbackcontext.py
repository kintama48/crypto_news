from queue import Queue
from typing import (
    TYPE_CHECKING,
    Dict,
    List,
    Match,
    NoReturn,
    Optional,
    Tuple,
    Union,
    Generic,
    Type,
    TypeVar,
)

from telegram import Update, CallbackQuery
from telegram.ext import ExtBot
from telegram.ext.utils.types import UD, CD, BD

if TYPE_CHECKING:
    from telegram import Bot
    from telegram.ext import Dispatcher, Job, JobQueue

CC = TypeVar('CC', bound='CallbackContext')


class CallbackContext(Generic[UD, CD, BD]):
    __slots__ = (
        '_dispatcher',
        '_chat_id_and_data',
        '_user_id_and_data',
        'args',
        'matches',
        'error',
        'job',
        'async_args',
        'async_kwargs',
        '__dict__',
    )

    def __init__(self, dispatcher: 'Dispatcher'):
        """
        Args:
            dispatcher (:class:`telegram.ext.Dispatcher`):
        """
        if not dispatcher.use_context:
            raise ValueError(
                'CallbackContext should not be used with a non context aware ' 'dispatcher!'
            )
        self._dispatcher = dispatcher
        self._chat_id_and_data: Optional[Tuple[int, CD]] = None
        self._user_id_and_data: Optional[Tuple[int, UD]] = None
        self.args: Optional[List[str]] = None
        self.matches: Optional[List[Match]] = None
        self.error: Optional[Exception] = None
        self.job: Optional['Job'] = None
        self.async_args: Optional[Union[List, Tuple]] = None
        self.async_kwargs: Optional[Dict[str, object]] = None

    @property
    def dispatcher(self) -> 'Dispatcher':
        """:class:`telegram.ext.Dispatcher`: The dispatcher associated with this context."""
        return self._dispatcher

    @property
    def bot_data(self) -> BD:
        """:obj:`dict`: Optional. A dict that can be used to keep any data in. For each
        update it will be the same ``dict``.
        """
        return self.dispatcher.bot_data

    @bot_data.setter
    def bot_data(self, value: object) -> NoReturn:
        raise AttributeError(
            "You can not assign a new value to bot_data, see https://git.io/Jt6ic"
        )

    @property
    def chat_data(self) -> Optional[CD]:
        """:obj:`dict`: Optional. A dict that can be used to keep any data in. For each
        update from the same chat id it will be the same ``dict``.

        Warning:
            When a group chat migrates to a supergroup, its chat id will change and the
            ``chat_data`` needs to be transferred. For details see our `wiki page
            <https://github.com/python-telegram-bot/python-telegram-bot/wiki/
            Storing-bot,-user-and-chat-related-data#chat-migration>`_.
        """
        if self._chat_id_and_data:
            return self._chat_id_and_data[1]
        return None

    @chat_data.setter
    def chat_data(self, value: object) -> NoReturn:
        raise AttributeError(
            "You can not assign a new value to chat_data, see https://git.io/Jt6ic"
        )

    @property
    def user_data(self) -> Optional[UD]:
        """:obj:`dict`: Optional. A dict that can be used to keep any data in. For each
        update from the same user it will be the same ``dict``.
        """
        if self._user_id_and_data:
            return self._user_id_and_data[1]
        return None

    @user_data.setter
    def user_data(self, value: object) -> NoReturn:
        raise AttributeError(
            "You can not assign a new value to user_data, see https://git.io/Jt6ic"
        )

    def refresh_data(self) -> None:
        """If :attr:`dispatcher` uses persistence, calls
        :meth:`telegram.ext.BasePersistence.refresh_bot_data` on :attr:`bot_data`,
        :meth:`telegram.ext.BasePersistence.refresh_chat_data` on :attr:`chat_data` and
        :meth:`telegram.ext.BasePersistence.refresh_user_data` on :attr:`user_data`, if
        appropriate.

        .. versionadded:: 13.6
        """
        if self.dispatcher.persistence:
            if self.dispatcher.persistence.store_bot_data:
                self.dispatcher.persistence.refresh_bot_data(self.bot_data)
            if self.dispatcher.persistence.store_chat_data and self._chat_id_and_data is not None:
                self.dispatcher.persistence.refresh_chat_data(*self._chat_id_and_data)
            if self.dispatcher.persistence.store_user_data and self._user_id_and_data is not None:
                self.dispatcher.persistence.refresh_user_data(*self._user_id_and_data)

    def drop_callback_data(self, callback_query: CallbackQuery) -> None:
        if isinstance(self.bot, ExtBot):
            if not self.bot.arbitrary_callback_data:
                raise RuntimeError(
                    'This telegram.ext.ExtBot instance does not use arbitrary callback data.'
                )
            self.bot.callback_data_cache.drop_data(callback_query)
        else:
            raise RuntimeError('telegram.Bot does not allow for arbitrary callback data.')

    @classmethod
    def from_error(
        cls: Type[CC],
        update: object,
        error: Exception,
        dispatcher: 'Dispatcher',
        async_args: Union[List, Tuple] = None,
        async_kwargs: Dict[str, object] = None,
    ) -> CC:
        self = cls.from_update(update, dispatcher)
        self.error = error
        self.async_args = async_args
        self.async_kwargs = async_kwargs
        return self

    @classmethod
    def from_update(cls: Type[CC], update: object, dispatcher: 'Dispatcher') -> CC:
        self = cls(dispatcher)

        if update is not None and isinstance(update, Update):
            chat = update.effective_chat
            user = update.effective_user

            if chat:
                self._chat_id_and_data = (
                    chat.id,
                    dispatcher.chat_data[chat.id],  # pylint: disable=W0212
                )
            if user:
                self._user_id_and_data = (
                    user.id,
                    dispatcher.user_data[user.id],  # pylint: disable=W0212
                )
        return self

    @classmethod
    def from_job(cls: Type[CC], job: 'Job', dispatcher: 'Dispatcher') -> CC:
        self = cls(dispatcher)
        self.job = job
        return self

    def update(self, data: Dict[str, object]) -> None:
        for key, value in data.items():
            setattr(self, key, value)

    @property
    def bot(self) -> 'Bot':
        return self._dispatcher.bot

    @property
    def job_queue(self) -> Optional['JobQueue']:
        return self._dispatcher.job_queue

    @property
    def update_queue(self) -> Queue:
        return self._dispatcher.update_queue

    @property
    def match(self) -> Optional[Match[str]]:
        try:
            return self.matches[0]  # type: ignore[index] # pylint: disable=unsubscriptable-object
        except (IndexError, TypeError):
            return None
