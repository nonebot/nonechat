from typing import TYPE_CHECKING
from abc import ABC, abstractmethod

from .info import User, Event, MessageEvent

if TYPE_CHECKING:
    from .app import Frontend


class Backend(ABC):
    frontend: "Frontend"

    def __init__(self, frontend: "Frontend"):
        self.frontend = frontend

    @abstractmethod
    def on_console_init(self):
        ...

    @abstractmethod
    def on_console_load(self):
        ...

    @abstractmethod
    def on_console_mount(self):
        ...

    @abstractmethod
    def on_console_unmount(self):
        ...

    @abstractmethod
    async def build_message_event(self, message: str, user: User) -> MessageEvent:
        ...

    @abstractmethod
    async def post_event(self, event: Event):
        ...
