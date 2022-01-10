import re
import warnings
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Tuple, TypeVar, Union

from telegram import MessageEntity, Update
from telegram.ext import BaseFilter, Filters
from telegram.utils.deprecate import TelegramDeprecationWarning
from telegram.utils.types import SLT
from telegram.utils.helpers import DefaultValue, DEFAULT_FALSE

from .utils.types import CCT
from .handler import Handler

if TYPE_CHECKING:
    from telegram.ext import Dispatcher

RT = TypeVar('RT')


class CommandHandler(Handler[Update, CCT]):
    __slots__ = ('command', 'filters', 'pass_args')

    def __init__(
        self,
        command: SLT[str],
        callback: Callable[[Update, CCT], RT],
        filters: BaseFilter = None,
        allow_edited: bool = None,
        pass_args: bool = False,
        pass_update_queue: bool = False,
        pass_job_queue: bool = False,
        pass_user_data: bool = False,
        pass_chat_data: bool = False,
        run_async: Union[bool, DefaultValue] = DEFAULT_FALSE,
    ):
        super().__init__(
            callback,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data,
            run_async=run_async,
        )

        if isinstance(command, str):
            self.command = [command.lower()]
        else:
            self.command = [x.lower() for x in command]
        for comm in self.command:
            if not re.match(r'^[\da-z_]{1,32}$', comm):
                raise ValueError('Command is not a valid bot command')

        if filters:
            self.filters = Filters.update.messages & filters
        else:
            self.filters = Filters.update.messages

        if allow_edited is not None:
            warnings.warn(
                'allow_edited is deprecated. See https://git.io/fxJuV for more info',
                TelegramDeprecationWarning,
                stacklevel=2,
            )
            if not allow_edited:
                self.filters &= ~Filters.update.edited_message
        self.pass_args = pass_args

    def check_update(
        self, update: object
    ) -> Optional[Union[bool, Tuple[List[str], Optional[Union[bool, Dict]]]]]:
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message

            if (
                message.entities
                and message.entities[0].type == MessageEntity.BOT_COMMAND
                and message.entities[0].offset == 0
                and message.text
                and message.bot
            ):
                command = message.text[1 : message.entities[0].length]
                args = message.text.split()[1:]
                command_parts = command.split('@')
                command_parts.append(message.bot.username)

                if not (
                    command_parts[0].lower() in self.command
                    and command_parts[1].lower() == message.bot.username.lower()
                ):
                    return None

                filter_result = self.filters(update)
                if filter_result:
                    return args, filter_result
                return False
        return None

    def collect_optional_args(
        self,
        dispatcher: 'Dispatcher',
        update: Update = None,
        check_result: Optional[Union[bool, Tuple[List[str], Optional[bool]]]] = None,
    ) -> Dict[str, object]:
        optional_args = super().collect_optional_args(dispatcher, update)
        if self.pass_args and isinstance(check_result, tuple):
            optional_args['args'] = check_result[0]
        return optional_args

    def collect_additional_context(
        self,
        context: CCT,
        update: Update,
        dispatcher: 'Dispatcher',
        check_result: Optional[Union[bool, Tuple[List[str], Optional[bool]]]],
    ) -> None:
        if isinstance(check_result, tuple):
            context.args = check_result[0]
            if isinstance(check_result[1], dict):
                context.update(check_result[1])


class PrefixHandler(CommandHandler):
    __slots__ = ('_prefix', '_command', '_commands')

    def __init__(
        self,
        prefix: SLT[str],
        command: SLT[str],
        callback: Callable[[Update, CCT], RT],
        filters: BaseFilter = None,
        pass_args: bool = False,
        pass_update_queue: bool = False,
        pass_job_queue: bool = False,
        pass_user_data: bool = False,
        pass_chat_data: bool = False,
        run_async: Union[bool, DefaultValue] = DEFAULT_FALSE,
    ):

        self._prefix: List[str] = []
        self._command: List[str] = []
        self._commands: List[str] = []

        super().__init__(
            'nocommand',
            callback,
            filters=filters,
            allow_edited=None,
            pass_args=pass_args,
            pass_update_queue=pass_update_queue,
            pass_job_queue=pass_job_queue,
            pass_user_data=pass_user_data,
            pass_chat_data=pass_chat_data,
            run_async=run_async,
        )

        self.prefix = prefix  # type: ignore[assignment]
        self.command = command  # type: ignore[assignment]
        self._build_commands()

    @property
    def prefix(self) -> List[str]:
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: Union[str, List[str]]) -> None:
        if isinstance(prefix, str):
            self._prefix = [prefix.lower()]
        else:
            self._prefix = prefix
        self._build_commands()

    def command(self) -> List[str]:
        return self._command

    @command.setter
    def command(self, command: Union[str, List[str]]) -> None:
        if isinstance(command, str):
            self._command = [command.lower()]
        else:
            self._command = command
        self._build_commands()

    def _build_commands(self) -> None:
        self._commands = [x.lower() + y.lower() for x in self.prefix for y in self.command]

    def check_update(
        self, update: object
    ) -> Optional[Union[bool, Tuple[List[str], Optional[Union[bool, Dict]]]]]:
        if isinstance(update, Update) and update.effective_message:
            message = update.effective_message

            if message.text:
                text_list = message.text.split()
                if text_list[0].lower() not in self._commands:
                    return None
                filter_result = self.filters(update)
                if filter_result:
                    return text_list[1:], filter_result
                return False
        return None
