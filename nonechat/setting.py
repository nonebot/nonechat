from warnings import warn
from dataclasses import dataclass

from textual.color import Color


@dataclass
class ConsoleSetting:
    title: str = "Console"
    sub_title: str = "powered by Textual"
    room_title: str | None = None
    title_color: Color | None = None
    icon: str | None = None
    icon_color: Color | None = None

    bg_color: Color | None = None
    header_color: Color | None = None
    dark_bg_color: Color | None = None
    dark_header_color: Color | None = None

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
