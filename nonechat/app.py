import sys
import contextlib
from datetime import datetime
from typing_extensions import TypeVar
from typing import Union, TextIO, Generic, Optional, cast

from textual.app import App
from textual.widget import Widget
from textual.widgets import Input
from textual.binding import Binding
from textual.message import Message

from .backend import Backend
from .router import RouterView
from .setting import ConsoleSetting
from .views.log_view import LogView
from .components.footer import Footer
from .components.header import Header
from .message import Text, ConsoleMessage
from .log_redirect import FakeIO, LogStorage
from .views.horizontal import HorizontalView
from .model import Event, Robot, Channel, MessageEvent

TB = TypeVar("TB", bound=Backend, default=Backend)


class BotModeChanged(Message):
    def __init__(self, is_bot_mode: bool) -> None:
        super().__init__()
        self.is_bot_mode = is_bot_mode


class Frontend(App, Generic[TB]):
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=False, priority=True),
        Binding("ctrl+d", "toggle_dark", "Toggle dark mode"),
        Binding("ctrl+s", "screenshot", "Save a screenshot"),
        Binding("ctrl+underscore", "focus_input", "Focus input", key_display="ctrl+/"),
        Binding("ctrl+b", "toggle_bot_mode", "Toggle bot mode", key_display="ctrl+b"),
    ]

    ROUTES = {"main": lambda: HorizontalView(), "log": lambda: LogView()}

    def __init__(self, backend: type[TB], setting: ConsoleSetting = ConsoleSetting(), bot_mode: bool = False):
        super().__init__()
        self.setting = setting
        self.title = setting.title  # type: ignore
        self.sub_title = setting.sub_title  # type: ignore

        self.log_store = LogStorage()

        self._fake_output = cast(TextIO, FakeIO(self.log_store))
        self._origin_stdout = sys.stdout
        self._origin_stderr = sys.stderr
        self._textual_stdout: Optional[TextIO] = None
        self._textual_stderr: Optional[TextIO] = None
        self.backend: TB = backend(self)

        # Bot 模式状态
        self.is_bot_mode = bot_mode
        self.bot_mode_watchers: list[Widget] = []

    def compose(self):
        yield Header()
        yield RouterView(self.ROUTES, "main")
        yield Footer()

    def on_load(self):
        self.backend.on_console_load()

    async def on_mount(self):
        with contextlib.suppress(Exception):
            self._textual_stdout = sys.stdout
            sys.stdout = self._fake_output

        with contextlib.suppress(Exception):
            self._textual_stderr = sys.stderr
            sys.stderr = self._fake_output

        # 应用主题背景色
        self.apply_theme_background()

        await self.backend.on_console_mount()
        await self.backend.add_user(self.backend.current_user)
        await self.backend.add_channel(self.backend.current_channel)
        await self.backend.add_bot(self.backend.current_bot)

    async def on_unmount(self):
        if self._textual_stdout is not None:
            sys.stdout = self._origin_stdout
        if self._textual_stderr is not None:
            sys.stderr = self._origin_stderr
        await self.backend.on_console_unmount()

    async def send_message(
        self,
        content: ConsoleMessage,
        channel: Union[Channel, None] = None,
        bot: Union[Robot, None] = None,
    ):
        """发送消息到当前频道或指定频道"""
        target = channel or self.backend.current_channel
        if (
            not self.is_bot_mode
            and target.id != self.backend.current_channel.id
            and target.id == f"private:{self.backend.current_user.id}"
        ):
            self.notify(
                f"Message from {(bot or self.backend.current_bot).nickname}: {content!s}",
                title="New Message",
                timeout=1,
            )
        msg = MessageEvent(
            time=datetime.now(),
            self_id=(bot or self.backend.current_bot).id,
            type="console.message",
            user=(bot or self.backend.current_bot),
            message_id="_unset_",
            message=content,
            channel=target,
        )
        return await self.backend.write_chat(msg, target)

    async def receive_message(self, message: "MessageEvent"):
        """接收消息"""
        if (
            message.channel.id != self.backend.current_channel.id
            and message.channel.id == f"private:{self.backend.current_user.id}"
        ):
            self.notify(
                f"Message from {self.backend.current_bot.nickname}: {message.message!s}",
                title="New Message",
            )
        await self.backend.add_user(message.user)
        await self.backend.add_channel(message.channel)
        return await self.backend.write_chat(message, message.channel)

    async def recall_message(self, message_id: str, channel: Union[Channel, None] = None):
        """撤回消息"""
        channel = channel or self.backend.current_channel
        return await self.backend.remove_chat(message_id, channel)

    async def edit_message(
        self, message_id: str, content: ConsoleMessage, channel: Union[Channel, None] = None
    ):
        """编辑消息"""
        channel = channel or self.backend.current_channel
        return await self.backend.edit_chat(message_id, content, channel)

    async def toggle_bell(self):
        await self.run_action("bell")

    def action_focus_input(self):
        with contextlib.suppress(Exception):
            self.query_one(Input).focus()

    async def action_post_message(self, message: str):
        msg = MessageEvent(
            time=datetime.now(),
            self_id=self.backend.current_bot.id,
            type="console.message",
            user=self.backend.current_bot if self.is_bot_mode else self.backend.current_user,
            message_id="_unset_",
            message=ConsoleMessage([Text(message)]),
            channel=self.backend.current_channel,
        )
        ans = await self.backend.write_chat(
            msg,
            self.backend.current_channel,
        )
        # 在普通模式下触发 post_event
        if not self.is_bot_mode:
            await self.backend.post_event(msg)
        return ans

    async def action_post_event(self, event: Event):
        await self.backend.post_event(event)

    async def action_toggle_bot_mode(self) -> None:
        """切换机器人模式"""
        self.is_bot_mode = not self.is_bot_mode
        if self.is_bot_mode:
            self.notify("Bot mode activated", title="Mode Changed")
        else:
            self.notify("User mode activated", title="Mode Changed")

        # self.post_message(BotModeChanged(self.is_bot_mode))
        for watcher in self.bot_mode_watchers:
            watcher.post_message(BotModeChanged(self.is_bot_mode))

    def action_toggle_dark(self) -> None:
        """切换暗色模式并应用相应背景色"""
        # 先调用父类的 toggle_dark 方法
        super().action_toggle_dark()

        # 应用对应的背景色
        self.apply_theme_background()

    def apply_theme_background(self) -> None:
        """根据当前主题模式应用背景色设置"""
        setting = self.setting

        # 查找需要更新背景色的视图
        try:
            view = self.query_one(RouterView)
            if self.current_theme.dark:
                view.styles.background = setting.dark_bg_color
            else:
                view.styles.background = setting.bg_color
        except Exception:
            # 视图可能还没有加载
            pass

        # 如果有其他需要设置背景色的组件，可以在这里添加
        try:
            hd = self.query_one(Header)
            if self.current_theme.dark:
                hd.styles.background = setting.dark_header_color
            else:
                hd.styles.background = setting.header_color
        except Exception:
            # 视图可能还没有加载
            pass
