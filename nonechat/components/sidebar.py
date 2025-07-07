from typing import TYPE_CHECKING, cast

from textual.widget import Widget
from textual.containers import Vertical
from textual.message import Message

from .user_selector import UserSelector, UserSelectorPressed
from .channel_selector import ChannelSelector, ChannelSelectorPressed

if TYPE_CHECKING:
    from ..app import Frontend


class SidebarUserChanged(Message):
    """侧边栏用户更改消息"""
    
    def __init__(self, user) -> None:
        super().__init__()
        self.user = user


class SidebarChannelChanged(Message):
    """侧边栏频道更改消息"""
    
    def __init__(self, channel) -> None:
        super().__init__()
        self.channel = channel


class Sidebar(Widget):
    """侧边栏组件，包含用户和频道选择器"""
    
    DEFAULT_CSS = """
    Sidebar {
        layout: vertical;
        width: 25%;
        height: auto;
        border-right: solid rgba(170, 170, 170, 0.7);
        background: rgba(40, 44, 52, 0.3);
        padding: 1;
    }
    
    Sidebar UserSelector {
        height: 45%;
        margin-bottom: 1;
    }
    
    Sidebar ChannelSelector {
        height: 45%;
    }
    """
    
    def __init__(self):
        super().__init__()
        self.user_selector = UserSelector()
        self.channel_selector = ChannelSelector()
    
    @property
    def app(self) -> "Frontend":
        return cast("Frontend", super().app)
    
    def compose(self):
        yield self.user_selector
        yield self.channel_selector
    
    def on_user_selector_pressed(self, event: UserSelectorPressed):
        """处理用户选择事件"""
        # 更新当前用户
        self.app.storage.set_user(event.user)
        
        # 更新用户选择器显示
        self.user_selector.update_user_list()
        
        # 向父组件发送消息
        self.post_message(SidebarUserChanged(event.user))
    
    def on_channel_selector_pressed(self, event: ChannelSelectorPressed):
        """处理频道选择事件"""
        # 更新当前频道
        self.app.storage.set_channel(event.channel)
        
        # 更新频道选择器显示
        self.channel_selector.update_channel_list()
        
        # 向父组件发送消息
        self.post_message(SidebarChannelChanged(event.channel))
    
    def update_displays(self):
        """更新显示"""
        self.user_selector.update_user_list()
        self.channel_selector.update_channel_list()
