from textual.widgets import Header as TextualHeader
class Header(TextualHeader):
    DEFAULT_CSS = """
    Header {
        background: rgba(90, 99, 108, 0.6);
    }
    Header > HeaderIcon {
    }
    Header > HeaderTitle {
        color: rgba(229, 192, 123, 1);
    }
    """

    def __init__(self):
        super().__init__(show_clock=True)
