"""Contains the variable screens, such as modifying a variable or deleting it"""

import re

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import Input, Label, Tree, Button, RadioSet

from nix_tree.help_screens import OptionsHelpScreen
from nix_tree.parsing import Types


class ModifyScreen(ModalScreen[str]):
    """This screen is brought up when the user attempts to modify a variable"""
    BINDINGS = [
        ("escape", "quit_pressed")
    ]

    def __init__(self, node: Tree.NodeSelected) -> None:
        """Redefines the init function of a screen - polymorphism - to store required variables

        Args:
            node: Tree.NodeSelected - the node that is being modified
        """

        self.__node = node
        if node.node.data:
            self.__path, self.__value = (list(node.node.data.keys())[0], list(node.node.data.values())[0])
            self.__type: Types = node.node.data.get("type")
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the modify screen will look like (it heavily depends on the variable type)

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Center():
            if self.__type == Types.BOOL:
                yield RadioSet(
                    "true",
                    "false",
                )
            elif self.__type == Types.INT:
                yield Input(value=self.__value, type="integer")
            elif self.__type == Types.LIST:
                self.notify("Ensure you keep the square brackets and speech marks for string")
                yield Input(value=self.__value)
            elif self.__type == Types.STRING:
                self.notify("Ensure you keep the speech marks for a string")
                yield Input(value=self.__value, type="text")
            else:
                yield Input(value=self.__value, type="text")

    def on_input_submitted(self, new_data: Input.Submitted) -> None:
        """Takes the user input from the input widget and performs the modification while also creating the operations
        stack message

        Args:
            new_data: Input.Submitted - the user input in the input widget

        Note:
            It also performs a small bit of input validation using regex.
            This function is only called if the user edits the variable with an input screen - hence it is only called
            for integers, strings, lists and unique variables!
        """

        if self.__value != new_data.value:
            if self.__type == Types.LIST and (not re.search(r"\A\[.+]\Z", new_data.value)):
                self.notify("You lost a bracket! Not updating")
                self.app.pop_screen()
            elif self.__type == Types.STRING and (not re.search(r"\A'.+'\Z", new_data.value)):
                self.notify("You lost a speech mark! Not updating")
                self.app.pop_screen()
            else:
                clean_input: str = re.sub(r"(\[)(\s*)", "[ ", new_data.value)
                clean_input: str = re.sub(r"(\s*)(\])", " ]", clean_input)
                self.__node.node.label = self.__path.split(".")[-1] + "=" + clean_input
                if self.__node.node.data:
                    self.__node.node.data[self.__path] = clean_input
                self.dismiss(f"Change {self.__path}={self.__value} -> "
                             f"{self.__path}={clean_input}")
        else:
            self.app.pop_screen()

    def on_radio_set_changed(self, selected: RadioSet.Changed):
        """Takes the user input from the radio_set widget and performs the modification to the variable alongside
        creating the operations stack message

        Args:
            selected: RadioSet.Changed - the radio item the user chose (true or false)

        Note:
            As with on_input_submitted this only gets called for boolean modifications
        """

        if self.__value != selected.pressed.label.plain:
            self.__node.node.label = self.__path.split(".")[-1] + "=" + selected.pressed.label.plain
            if self.__node.node.data:
                self.__node.node.data[self.__path] = selected.pressed.label.plain
            self.dismiss(f"Change {self.__path}={self.__value} -> {self.__path}={selected.pressed.label.plain}")
        else:
            self.app.pop_screen()

    def action_quit_pressed(self) -> None:
        """Quits the screen when one of the quit buttons are pressed"""

        self.app.pop_screen()


class OptionsScreen(ModalScreen[str]):
    """The screen brought up when the user selects a node, it provides the options
    such as modifying or deleting the node"""

    BINDINGS = [
        ("q", "quit_pressed"),
        ("escape", "quit_pressed"),
        ("?", "help", "Show help screen"),
    ]

    def __init__(self, node: Tree.NodeSelected) -> None:
        """Redefines the init function of a screen - polymorphism - to store required variables

        Args:
            node: Tree.NodeSelected - the node that is being modified
        """

        self.__node = node
        if node.node.data:
            self.__path, self.__value = (list(node.node.data.keys())[0], list(node.node.data.values())[0])
            self.__type: str = node.node.data.get("type")
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the options screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Vertical(classes="modifytext"):
            with Center():
                yield Label(self.__path, classes="box")
            with Center():
                yield Label(f"Current value: {self.__value}")
            with Horizontal(id="buttons"):
                yield Button("Delete", id="delete", variant="error")
                yield Button("Modify", id="modify", variant="primary")
                yield Button("Exit", id="exit", variant="default")
            with Center():
                yield Label("q/Esc: quit options, ?: Show help screen")

    def on_button_pressed(self, button: Button.Pressed) -> None:
        """When one of the buttons (delete, modify or exit) is called, this function manages their operations

        Args:
            button: Button.Pressed - stores the data about which button was pressed
        """

        if button.button.id == "exit":
            self.app.pop_screen()
        elif button.button.id == "delete":
            self.__node.node.remove()
            if self.__node.node.data:
                self.dismiss(f"Delete {self.__path}={self.__value} with type {self.__type}")
        else:
            def save_modify_changes(changes_made: str | None) -> None:
                if changes_made:
                    self.dismiss(changes_made)

            self.app.push_screen(ModifyScreen(self.__node), save_modify_changes)

    def action_quit_pressed(self) -> None:
        """Quits the screen when one of the quit buttons are pressed"""

        self.app.pop_screen()

    def action_help(self) -> None:
        """Brings up the options help screen"""

        self.app.push_screen(OptionsHelpScreen())
