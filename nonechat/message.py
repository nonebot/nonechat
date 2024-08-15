from abc import ABC, abstractmethod
from typing import Union, Optional, overload
from collections.abc import Iterator, Sequence
from dataclasses import field, asdict, dataclass

from rich.style import Style
from rich.segment import Segment
from rich.emoji import EmojiVariant
from rich.text import Text as RichText
from rich.emoji import Emoji as RichEmoji
from rich.markdown import Markdown as RichMarkdown
from rich.measure import Measurement, measure_renderables
from rich.console import Console, RenderResult, JustifyMethod, ConsoleOptions


class Element(ABC):
    @property
    @abstractmethod
    def rich(self) -> Union[RichText, RichEmoji, RichMarkdown]:
        pass

    def __str__(self) -> str:
        return str(self.rich)

    def __rich_console__(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        yield self.rich

    def __rich_measure__(self, console: "Console", options: "ConsoleOptions") -> Measurement:
        return measure_renderables(console, options, (self.rich,))


class Text(Element):
    text: str

    def __init__(self, text: str) -> None:
        """实例化一个 Text 消息元素, 用于承载消息中的文字.

        Args:
            text (str): 元素所包含的文字
        """
        self.text = text

    @property
    def rich(self) -> RichText:
        return RichText(self.text, end="")


class Emoji(Element):
    name: str

    def __init__(self, name: str):
        self.name = name

    @property
    def rich(self) -> RichEmoji:
        return RichEmoji(self.name)


@dataclass
class Markup(Element):
    markup: str
    style: Union[str, Style] = field(default="none")
    emoji: bool = field(default=True)
    emoji_variant: Optional[EmojiVariant] = field(default=None)

    @property
    def rich(self) -> RichText:
        return RichText.from_markup(
            self.markup,
            style=self.style,
            emoji=self.emoji,
            emoji_variant=self.emoji_variant,
            end="",
        )


@dataclass
class Markdown(Element):
    markup: str
    code_theme: str = field(default="monokai")
    justify: Optional[JustifyMethod] = field(default=None)
    style: Union[str, Style] = field(default="none")
    hyperlinks: bool = field(default=True)
    inline_code_lexer: Optional[str] = field(default=None)
    inline_code_theme: Optional[str] = field(default=None)

    @property
    def rich(self) -> RichMarkdown:
        return RichMarkdown(**asdict(self))

    def __str__(self) -> str:
        return str(
            RichText.from_markup(
                self.markup,
                style=self.style,
                end="",
            )
        )


class ConsoleMessage(Sequence[Element]):
    @overload
    def __getitem__(self, index: int) -> Element: ...

    @overload
    def __getitem__(self, index: slice) -> Sequence[Element]: ...

    def __getitem__(self, index: Union[int, slice]) -> Union[Element, Sequence[Element]]:
        return self.content[index]

    def __len__(self) -> int:
        return len(self.content)

    content: list[Element]

    def __init__(self, elements: list[Element]):
        """从传入的序列(可以是元组 tuple, 也可以是列表 list) 创建消息链.
        Args:
            elements (list[T]): 包含且仅包含消息元素的序列
        Returns:
            MessageChain: 以传入的序列作为所承载消息的消息链
        """
        self.content = elements

    def __iter__(self) -> Iterator[Element]:
        yield from self.content

    def __reversed__(self) -> Iterator[Element]:
        yield from reversed(self.content)

    def __rich_console__(self, console: "Console", options: "ConsoleOptions") -> "RenderResult":
        yield from self
        if self.content and not isinstance(self.content[-1], Markdown):
            yield Segment("\n")

    def __rich_measure__(self, console: "Console", options: "ConsoleOptions") -> Measurement:
        measurements = [Measurement.get(console, options, element) for element in self]
        return Measurement(sum(i.minimum for i in measurements), sum(i.maximum for i in measurements))

    def __str__(self):
        return "".join(map(str, self.content))
