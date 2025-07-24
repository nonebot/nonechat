from warnings import warn
from typing import Optional
from dataclasses import dataclass

from textual.color import Color


@dataclass
class ConsoleSetting:
    title: str = "Console"
    sub_title: str = "powered by Textual"
    room_title: Optional[str] = None
    title_color: Optional[Color] = None
    icon: Optional[str] = None
    icon_color: Optional[Color] = None

    bg_color: Optional[Color] = None
    header_color: Optional[Color] = None
    dark_bg_color: Optional[Color] = None
    dark_header_color: Optional[Color] = None

    toolbar_exit: str = "⛔"
    toolbar_clear: str = "🗑️"
    toolbar_setting: str = "⚙️"
    toolbar_log: str = "📝"
    toolbar_fold: str = "⏪"
    toolbar_expand: str = "⏩"
    user_avatar: str = "👤"
    user_name: str = "User"
    bot_avatar: str = "🤖"
    bot_name: str = "Bot"

    new_message_color: str = "lime blink"

    def __post_init__(self):
        if self.room_title is not None:
            warn(
                "room_title is deprecated.",
                UserWarning,
                stacklevel=3,
            )
