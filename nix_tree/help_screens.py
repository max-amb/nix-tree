"""Contains the help screens for the UI"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Markdown

# The help text for the main menu
MAINHELPTEXT = """\
#  *Help*

- Tab: To switch from tabs to the window
- Enter: To modify a variable or fold an indent
- q/Esc : To close this help dialog

Note:
Lists have spaces placed at the front of them to avoid formatting issues,
they will not be present in the final file.
"""

# The help text for the options menu
OPTIONSHELPTEXT = """\
# *Options help*

- Tab: To switch between buttons
- Enter: To select one of the buttons
- q/Esc: To close this help dialog or the options dialog
- Delete: To delete that node/variable
- Modify: To modify that variables data
- Exit: To close the options dialog
"""

# The help text for the section options menu
SECTIONOPTIONSHELPTEXT = """\
# *Section options help*

- Tab: To switch between buttons
- Enter: To select one of the buttons
- q/Esc: To close this help dialog or the options dialog
- Delete: To delete that section 
- Add: To add a variable/section 
- Exit: To close the options dialog
"""

class HelpScreen(ModalScreen):
    """The outline for a help screen in the app"""

    # Defines the key presses that perform actions in the window
    BINDINGS = [
        ("q", "quit_pressed"),
        ("escape", "quit_pressed"),
    ]

    def action_quit_pressed(self) -> None:
        """Quits the app when one of the quit buttons are pressed"""

        self.app.pop_screen()


class MainHelpScreen(HelpScreen):
    """Defines the help screen for the main window of the app"""

    def compose(self) -> ComposeResult:
        """Displays the markdown in MAINHELPTEXT"""

        yield Markdown(MAINHELPTEXT, id="mainhelptext")


class OptionsHelpScreen(HelpScreen):
    """Defines the help screen for the options window of the app (when selecting a variable)"""

    def compose(self) -> ComposeResult:
        """Displays the markdown in OPTIONSHELPTEXT"""

        yield Markdown(OPTIONSHELPTEXT, id="optionshelptext")


class SectionOptionsHelpScreen(HelpScreen):
    """Defines the help screen for the section options window of the app"""

    def compose(self) -> ComposeResult:
        """Displays the markdown in SECTIONOPTIONSHELPTEXT"""
        yield Markdown(SECTIONOPTIONSHELPTEXT, id="sectionoptionshelptext")
