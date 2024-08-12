"""Ui tests"""
from parsing import ParsingOptions, Types
from decomposer import DecomposerTree, Decomposer
from help_screens import MainHelpScreen, OptionsHelpScreen, SectionOptionsHelpScreen
from custom_types import *

from pathlib import Path
import re
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListView, ListItem, OptionList, Tree, Header, Footer, TabbedContent, \
    TabPane, Button, RadioSet

# Connector nodes are used in cases where it isn't known which node should be returned

OPTIONS_LOCATION: str = "/home/max/options.json"


class OperationsStack:
    """An implementation of the stack data-structure in order to store operations effectively"""

    def __init__(self) -> None:
        """Creates the stack and the stack variables"""

        self.__stack_array: list[ListItem] = []

    def pop(self) -> ListItem:
        """Pops the tops element of the stack

        Returns:
            ListItem - the top most element in the stack
        """

        return self.__stack_array.pop()

    def push(self, item: ListItem) -> None:
        """Pushes an element on to the stack

        Args:
            item: ListItem - the item to be added to the stack
        """

        self.__stack_array.append(item)

    def peek(self) -> ListItem:
        """Returns the uppermost value in the stack without removing it

        Returns:
            ListItem - the top most element in the stack
        """

        return self.__stack_array[-1]

    def get_len(self) -> int:
        """Returns the full stacks length

        Returns:
            int - the full stacks length
        """

        return len(self.__stack_array)


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
                yield Input(placeholder=self.__value, type="integer")
            elif self.__type == Types.LIST:
                self.notify("Ensure you keep the square brackets and speech marks for string")
                yield Input(placeholder=self.__value)
            elif self.__type == Types.STRING:
                self.notify("Ensure you keep the speech marks for a string")
                yield Input(placeholder=self.__value, type="text")
            else:
                yield Input(placeholder=self.__value, type="text")

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
                self.__node.node.label = self.__path.split(".")[-1] + "=" + new_data.value
                if self.__node.node.data:
                    self.__node.node.data[self.__path] = new_data.value
                self.dismiss(f"Change {self.__path}={self.__value} -> {self.__path}={new_data.value}")
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


def work_out_full_path(current_node: UIConnectorNode, path: list) -> list:
    """A function when given a node, works out its full path using parent relations

    Args:
        current_node: UIConnectorNode - the current node we are checking
        path: list - the path we have built up so far (needs to be stored for recursion)

    Returns:
        list - the path the function has calculated

    Note:
        The function does this utilising simple recursion - its interesting how much easier stuff is with recursion as
        it would have been a lot more complicated without
    """

    if not current_node.is_root:
        path.insert(0, current_node.label.plain)
        path = work_out_full_path(current_node.parent, path)
    return path


class AddScreenBoolean(ModalScreen[str]):
    """The add variable screen for a boolean"""

    def compose(self) -> ComposeResult:
        """Defines what the add variable screen for a boolean will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Center():
            yield RadioSet(
                "true",
                "false"
            )

    def on_radio_set_changed(self, selected: RadioSet.Changed):
        """Returns the user selection to the path input screen

        Args:
            selected: RadioSet.Changed - the choice of the user
        """

        self.dismiss(selected.pressed.label.plain)
        return


class AddScreenStringUniqueList(ModalScreen[str]):
    """The add variable screen for a string, a unique, or a list"""

    def compose(self) -> ComposeResult:
        """Defines what the add screen for a string, a unique or a list will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Center():
            yield Input()

    def on_input_submitted(self, user_input: Input.Submitted):
        """Returns the user selection to the path input screen

        Args:
            user_input: Input.Submitted - the choice of the user
        """

        self.dismiss(user_input.value)
        return


class AddScreenGroup(ModalScreen[list]):
    """The add group screen - called when a group is being added to another group (or section)"""

    def __init__(self, node: Tree.NodeSelected) -> None:
        """Redefining the init function (polymorphism) to store the required variables

        Args:
            node: Tree.NodeSelected - the node that we will connect the new group to
        """

        self.__node = node
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the add screen for a group will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Center():
            yield Input()

    def on_input_submitted(self, user_input: Input.Submitted) -> None:
        """Takes the user input from the Input widget and creates a group using it

        Args:
            user_input: Input.Submitted - the user input (their choice of name for the group)

        Note:
            If the section is being added to the root node, the second method of addition would put a dot at the
            start hence the if statement
        """
        self.__node.node.add(user_input.value)
        if self.__node.node.is_root:
            self.dismiss([f"Section {user_input.value} added"])
        else:
            full_path = '.'.join(work_out_full_path(self.__node.node, []))
            self.dismiss([f"Section {full_path}.{user_input.value} added"])
        return


class AddScreenInteger(ModalScreen[str]):
    """The add screen for creating an integer variable"""

    def compose(self) -> ComposeResult:
        """Defines what the add screen for an integer will look like

        Returns:
            ComposeResult - the screen in a form the library understands

        Note:
            using type="integer" restricts the input to the function to just numbers
        """

        with Center():
            yield Input(type="integer")

    def on_input_submitted(self, user_input: Input.Submitted):
        """Takes the users input to the Input widget and returns it to the path widget for addition

        Args:
            user_input: Input.Submitted - the users input for the variables data
        """

        self.dismiss(str(user_input.value))
        return


class AddScreenVariableSelection(ModalScreen[tuple[str, Types]]):
    """The screen where you can choose your variable type and it calls the appropriate method"""

    BINDINGS = [
        ("q", "quit_pressed"),
        ("escape", "quit_pressed"),
    ]

    def compose(self) -> ComposeResult:
        """Defines what the variable type selection (for adding variables) screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Center(classes="modifytext"):
            with Vertical():
                yield Label("Select the variables type")
                yield OptionList(
                    "boolean",
                    "string",
                    "integer",
                    "unique",
                    "list",
                )

    def on_option_list_option_selected(self, option_selected: OptionList.OptionSelected) -> None:
        """Takes in the option the user selected and saves the type, then calling the appropriate function to allow
        the user to input their variables data

        Args:
            option_selected: OptionList.OptionSelected - the option in the options list the user selected
        """

        def return_addition_for_stack(addition: str | None) -> None:
            """A function to return the data from the functions to the path screen

            Args:
                addition: str | None - contains the data from the variable data input functions
            """
            if addition:
                self.dismiss((addition, type_selected))

        match option_selected.option.prompt:
            case "boolean":
                type_selected = Types.BOOL
                self.app.push_screen(AddScreenBoolean(), return_addition_for_stack)
            case "string":
                type_selected = Types.STRING
                self.app.push_screen(AddScreenStringUniqueList(), return_addition_for_stack)
            case "unique":
                type_selected = Types.UNIQUE
                self.app.push_screen(AddScreenStringUniqueList(), return_addition_for_stack)
            case "list":
                type_selected = Types.LIST
                self.app.push_screen(AddScreenStringUniqueList(), return_addition_for_stack)
            case "integer":
                type_selected = Types.INT
                self.app.push_screen(AddScreenInteger(), return_addition_for_stack)

    def action_quit_pressed(self) -> None:
        """Quits the screen when one of the quit buttons are pressed"""

        self.app.pop_screen()


class AddScreenPath(ModalScreen[list]):
    """This is the screen where the user can input the path for the variable they would like to add"""

    BINDINGS = [
        ("escape", "quit_pressed"),
    ]

    def __init__(self, node: Tree.NodeSelected, options: ParsingOptions) -> None:
        """Redefining the init method as we need to store the current node and the data type the user would
        like to add

        Args:
            node: Tree.NodeSelected - the section from which they are creating the variable from
            options: ParsingOptions - an object that allows the path function to work out the required type
            of the variable the user wants to add

        Note:
            It also initialises a variable for later use, operations stores the operations that need to be added
            to the operations stack 
        """

        self.__node = node
        self.__operations = []
        self.__options = options
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the variable path input screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Vertical():
            with Center():
                self.notify("Enter path for the variable - e.g. firefox.enable or just enable")
                self.notify("This could be just the variable name or if you want it in a section/group use a .")
                self.notify("Note the section does not need to be created, this will create any section necessary")
                self.notify("If adding a group/section select the add group/section button")
                yield Input(placeholder="Type the path of the variable if adding a variable", id="path_input")
                with Center():
                    yield Button(label="Or add group/Section")
                    yield Label("Press ESC to go back")

    def on_input_submitted(self, path: Input.Submitted) -> None:
        """Manages the input from the user choosing a path to place the variable

        Args:
            path: Input.Submitted - the path the user  inputted

        Note:
            This method also does a small bit of input validation whereby if a list doesn't have all of its
            data between two brackets and a string between two speech marks, the data is invalid, and it does
            not get added
        """

        def handle_return_from_variable_addition(data: tuple[str | list, Types | None] | None) -> None:
            """Takes the data from variable addition and returns it back to the main class

            Args:
                data: tuple[str | list, Types | None] | None - the data, data[0] is either a string or a list - if it's
                a string then a variable needs to be added and hence it is validated and then added, if it is a list
                then it contains the operations that a group addition will lead to hence it can just be returned.
                Data[1] contains the data type of the variable if its being added
            """

            if data:
                if isinstance(data[0], list):  # It's a group being added
                    self.dismiss(data[0])
                    return
                if data[1] == Types.LIST and (not re.search(r"\A\[.+]\Z", data[0])):
                    self.notify("You lost a bracket! Not updating")
                    if type_as_defined:
                        self.app.push_screen(RecommendedTypeOrChooseType(type_as_defined),
                                             handle_return_from_variable_addition)
                    else:
                        self.app.push_screen(AddScreenVariableSelection(), handle_return_from_variable_addition)
                    pass
                elif data[1] == Types.STRING and (not re.search(r"\A'.+'\Z", data[0])):
                    self.notify("You lost a speech mark! Not updating")
                    if type_as_defined:
                        self.app.push_screen(RecommendedTypeOrChooseType(type_as_defined),
                                             handle_return_from_variable_addition)
                    else:
                        self.app.push_screen(AddScreenVariableSelection(), handle_return_from_variable_addition)
                    pass
                else:
                    path_as_list = work_out_full_path(self.__node.node, [])
                    node_added = self.recursive_addition(self.__node.node, path.value.split("."), data[0], path_as_list,
                                                         data[1])
                    if node_added:
                        if not path_as_list:  # If we are appending to root
                            self.__operations.append(f"Added {self.__path}={data[0]}")
                        else:
                            self.__operations.append(f"Added {'.'.join(path_as_list)}.{self.__path}={data[0]}")
                        self.dismiss(self.__operations)
            else:
                self.app.pop_screen()

        self.__path = path.value
        path_leading_up_to_section = ""
        if not self.__node.node.is_root:
            path_leading_up_to_section: str = '.'.join(work_out_full_path(self.__node.node, [])) + "."
        type_as_defined: tuple[Types, str] | None = self.__options.check_type(path_leading_up_to_section + path.value)
        if type_as_defined:
            self.app.push_screen(RecommendedTypeOrChooseType(type_as_defined),
                                 handle_return_from_variable_addition)
        else:
            self.app.push_screen(AddScreenVariableSelection(), handle_return_from_variable_addition)

    def on_button_pressed(self):
        """If a button has been pressed then a group has been added and hence the group addition function
        is called"""

        def return_group_addition_for_stack(operations: list | None):
            if operations:
                self.dismiss(operations)

        self.app.push_screen(AddScreenGroup(self.__node), return_group_addition_for_stack)

    def recursive_addition(self, node: UIConnectorNode, path: list, data: str, path_as_list: list,
                           data_type: Types) -> bool:
        """This recursive method works through the path the user specified and creates any required sections and at the
        end it also adds the variable to the tree

        Args:
            node: UIConnectorNode - the current node we are analysing (as the function is recursive this changes in every
            stack frame)
            path: list - this stores how far down the path the function is, also informing it when to stop
            data: str - the data of the variable to be added
            path_as_list: list - stores the path that needs to be added into the variables data (as it requires
            the full path)
            data_type: Types - the data type of the variable we are adding

        Returns:
            bool - true if the function added the variable and false if otherwise
        """
        if len(path) > 1:
            path_bit_already_exists = False
            for child in node.children:
                if child.label.plain == path[0]:
                    path_bit_already_exists = True
                    del path[0]
                    return self.recursive_addition(child, path, data, path_as_list, data_type)
            if not path_bit_already_exists:
                new_node = node.add(path[0])
                if new_node.parent.is_root:
                    self.__operations.append(f"Section {path[0]} added")
                else:
                    self.__operations.append(f"Section {'.'.join(work_out_full_path(new_node, []))} added")
                del path[0]
                return self.recursive_addition(new_node, path, data, path_as_list, data_type)
        else:
            var_already_exists = False
            for child in node.children:
                if child.label.plain.split("=")[0] == self.__path.split(".")[-1]:
                    var_already_exists = True
                    self.notify("variable already exists", severity="error")
                    return False
            if not var_already_exists:
                if not path_as_list:
                    node.add_leaf(self.__path.split(".")[-1] + "=" + data,
                                  data={self.__path: data, "type": data_type})
                else:
                    node.add_leaf(self.__path.split(".")[-1] + "=" + data,
                                  data={'.'.join(path_as_list) + "." + self.__path: data, "type": data_type})
                return True

    def action_quit_pressed(self) -> None:
        """Quits the screen when one of the quit buttons are pressed"""

        self.app.pop_screen()


class RecommendedTypeOrChooseType(ModalScreen[tuple[str, Types]]):
    """If a valid type has been found in the options.json this screen is pushed which asks the user if they would
    like to use the recommended type or chose their own"""

    BINDINGS = [
        ("q", "quit_pressed"),
        ("escape", "quit_pressed"),
    ]

    def __init__(self, recommended_type: tuple[Types, str]):
        """Redefines the init function of a screen - polymorphism - to store required variables

        Args:
            recommended_type: tuple[Types, str] - the type that has bbee
        """

        self.__recommended_type = recommended_type
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the Recommended type or choose type screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Vertical(classes="modifytext"):
            with Center():
                yield Label("A variable with that path has been found")
            with Horizontal(id="recommend_buttons"):
                yield Button(label="Use recommended type", id="recommended", variant="success")
                yield Button(label="Choose type (dangerous)", id="not_recommended", variant="error")

    def on_button_pressed(self, button: Button.Pressed) -> None:
        """Called when the user has decided to use the recommended type or to choose their own

        Args:
            button: Button.Pressed - contains the information pertaining to the option the user chose
        """

        def handle_return_from_variable_inputs(choice: str | None) -> None:
            """This handles the returns from variable input functions - if the user chooses to use the
            recommended type

            Args:
                choice: str | None - the users input in the variable input functions
            """

            if choice:
                self.dismiss((choice, self.__recommended_type[0]))
            else:
                self.app.pop_screen()

        def handle_return_from_variable_selection(choice: tuple[str, Types]):
            """This handles the return from the AddScreenVariableSelection screen, called if the user chooses their
            own data type

            Args:
                choice: tuple[str, Types] - the data from the screen - the string containing the user input and the
                Types contain the type they chose
            """

            if choice:
                self.dismiss(choice)
            else:
                self.app.pop_screen()

        if button.button.id == "recommended":
            self.notify(title="May or may not be helpful - what options.json says about this variable",
                        message=self.__recommended_type[1], timeout=5.0)
            match self.__recommended_type[0]:
                case Types.BOOL:
                    self.app.push_screen(AddScreenBoolean(), handle_return_from_variable_inputs)
                case Types.STRING:
                    self.notify("Ensure you keep data within string marks: ''")
                    self.app.push_screen(AddScreenStringUniqueList(), handle_return_from_variable_inputs)
                case Types.UNIQUE:
                    self.app.push_screen(AddScreenStringUniqueList(), handle_return_from_variable_inputs)
                case Types.LIST:
                    self.notify("Ensure you keep data within brackets: []")
                    self.app.push_screen(AddScreenStringUniqueList(), handle_return_from_variable_inputs)
                case Types.INT:
                    self.app.push_screen(AddScreenInteger(), handle_return_from_variable_inputs)
        else:
            self.app.push_screen(AddScreenVariableSelection(), handle_return_from_variable_selection)

    def action_quit_pressed(self) -> None:
        """Quits the screen when one of the quit buttons are pressed"""

        self.app.pop_screen()


class SectionOptionsScreen(ModalScreen[list[str]]):
    """The section options screen - brought up if one clicks on a section"""

    BINDINGS = [
        ("q", "quit_pressed"),
        ("escape", "quit_pressed"),
        ("?", "help", "Show help screen"),
    ]

    def __init__(self, node: Tree.NodeSelected, options: ParsingOptions) -> None:
        """Redefining the init function to take in variables (polymorphism) that are required, it also sets up 2 private
        attributes to be used later on

        Args:
            node: Tree.NodeSelected - the section node
            options: ParsingOptions - the options parser to work out the validity of a path
        """

        self.__node = node
        self.__options = options
        self.__operations = []
        self.__delete_already_clicked: bool = False
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the section options screen will look like (e.g. for adding a section)

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Vertical(classes="modifytext"):
            with Center():
                yield Label(f"Section: {self.__node.node.label}", classes="box")
            with Horizontal(id="buttons"):
                yield Button("Delete", id="delete_section", variant="error")
                yield Button("Add Child", id="add", variant="success")
                yield Button("Exit", id="exit_section", variant="default")
            with Center():
                yield Label("q/Esc: quit options, ?: Show help screen")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Called when the user decides what to do with the section by pressing a button, this calls appropriate
        functions or in deletions case it simply performs the deletion

        Args:
            event: Button.Pressed - the button the user chose
        """

        def return_addition_for_stack(changes: list | None) -> None:
            """Returns the changes from variable addition to the main class for addition to the operations stack

            Args:
                changes: list | None - the operations that have occurred in a list
            """

            if changes:
                self.dismiss(changes)
            else:
                self.app.pop_screen()

        if event.button.id == "exit_section":
            self.app.pop_screen()
        if event.button.id == "delete_section":
            if not self.__delete_already_clicked:
                self.notify("This will delete all of the options/variables and sections within this section",
                            severity="error")
                self.notify("If you are sure click delete again!", severity="error")
                self.__delete_already_clicked = True
            else:
                self.recursive_deletion(self.__node.node)
                self.dismiss(self.__operations)
        if event.button.id == "add":
            self.app.push_screen(AddScreenPath(self.__node, self.__options), return_addition_for_stack)
        else:
            pass

    def recursive_deletion(self, node: UIConnectorNode) -> None:
        """Recursively deletes a section by visiting children and then deleting all the data there and so on

        Args:
            node: UIConnectorNode - the current node being checked

        Note:
            It acts similarly to BFS in the way it iterates through sections
        """
        while node.children:
            for child in node.children:
                self.recursive_deletion(child)
        if not node.children and node.allow_expand:
            self.__operations.append(f"Section {'.'.join(work_out_full_path(node, []))} deleted")
            node.remove()
        if not node.children and not node.allow_expand:
            path, value = (list(node.data.keys())[0], list(node.data.values())[0])
            type_of_var: str = node.data.get("type")
            self.__operations.append(f"Delete {path}={value} type: {type_of_var}")
            node.remove()

    def action_quit_pressed(self) -> None:
        """Quits the screen when one of the quit buttons are pressed"""

        self.app.pop_screen()

    def action_help(self) -> None:
        """Brings up the help screen if the user requests help using ? or esc"""

        self.app.push_screen(SectionOptionsHelpScreen())


class UI(App):
    """Defines the main screen of the app"""

    """The path to the css"""
    CSS_PATH = "css.css"

    BINDINGS = [
        ("q", "quit", "To quit the app"),
        ("?", "help", "Show help screen"),
        ("u", "undo", "To undo the previous change"),
        ("e", "empty", "To empty the operations stack")
    ]

    def __init__(self, file_name: str, decomposer: Decomposer) -> None:
        """Redefining the init function to initialise two objects, the stack and the options parser,
        it also takes in the file name to place as the title of the tree

        Args:
            file_name: str - the file name
            decomposer: Decomposer - a decomposer object to form the tree
        """

        self.__stack = OperationsStack()
        self.__options = ParsingOptions(Path(OPTIONS_LOCATION))
        self.__file_name = file_name
        self.__decomposer = decomposer
        super().__init__()

    def setup_generations(self) -> Label:
        return Label("Placeholder for generation management")

    def action_help(self) -> None:
        """Calls the help screen if one of the help buttons are pressed"""

        self.push_screen(MainHelpScreen())

    def action_empty(self) -> None:
        """Empties the stack if the user chooses to empty the stack by pressing e"""

        while self.__stack.get_len() > 0:
            self.action_undo(empty_command=True)
        self.query_one("#operations_stack", ListView).clear()

    def action_undo(self, empty_command: bool = False) -> None:
        """Performs the undo commands by popping the change from the stack and reverse engineering it

        Args:
            empty_command: bool - if the command is part of an empty command it is more economical to simply clear the
            list instead of repeatedly popping from it
        """

        if self.__stack.get_len() > 0:
            if not empty_command:
                self.query_one("#operations_stack", ListView).pop(0)
            action: str | None = self.__stack.pop().name
            if action:
                if "[" in action:
                    path = action.split("=")[0].split(" ")[1]
                    variable: str = action[action.index("["):action.index("]") + 1]
                    full_path = path + "=" + variable
                elif "'" in action:
                    path = action.split("=")[0].split(" ")[1]
                    variable: str = "'" + action.split("'")[1] + "'"
                    full_path = path + "=" + variable
                else:
                    full_path = action.split(" ")[1]
                    path = full_path.split("=")[0]
                match action.split(" ")[0]:
                    case "Delete":
                        var_type = None
                        match action.split(" ")[-1]:
                            case "Types.LIST":
                                var_type = Types.LIST
                            case "Types.INT":
                                var_type = Types.INT
                            case "Types.STRING":
                                var_type = Types.STRING
                            case "Types.UNIQUE":
                                var_type = Types.UNIQUE
                            case "Types.BOOL":
                                var_type = Types.BOOL
                        if var_type:
                            self.recursive_addition(
                                self.query_one(Tree).root,
                                path.split("."),
                                full_path.split("=")[1],
                                var_type,
                                full_path.split("=")[0]
                            )
                        else:
                            raise Exception
                    case "Added":
                        variable = full_path.split("=")[1]
                        node_to_delete: UIVariableNode = self.recursive_searching_for_var(
                            self.query_one(Tree).root,
                            path.split("."),
                            variable
                        )
                        node_to_delete.remove()
                    case "Change":
                        change_command: str = action[7:]  # Can't use space splits as it changes the lists spaces
                        pre: list = change_command.split("->")[0].strip().split("=")
                        post: list = change_command.split("->")[1].strip().split("=")
                        variable_to_change: UIVariableNode = self.recursive_searching_for_var(
                            self.query_one(Tree).root,
                            post[0].split("."),
                            post[1]
                        )
                        new_label = f"{pre[0].split(".")[-1]}={pre[1]}"
                        variable_to_change.label = new_label
                        variable_to_change.data[post[0]] = pre[1]
                    case "Section":
                        match action.split(" ")[-1]:
                            case "deleted":
                                path_as_list = action.split(" ")[1].split(".")
                                if len(path_as_list) > 1:
                                    path_before_section = path_as_list[:-1]
                                else:
                                    path_before_section = path_as_list
                                section_node: UIConnectorNode = self.recursive_searching_for_connector(
                                    self.query_one(Tree).root,
                                    path_before_section
                                )
                                section_node.add(path_as_list[-1])
                            case "added":
                                path_as_list = action.split(" ")[1].split(".")
                                section_node: UIConnectorNode = self.recursive_searching_for_connector(
                                    self.query_one(Tree).root,
                                    path_as_list
                                )
                                section_node.remove()
        else:
            self.notify("The operations stack is empty")

    def recursive_addition(self, node: UIConnectorNode, path: list, data: str, data_type: Types,
                           full_path: str) -> None:
        """Called by the undo function - if a node has been deleted this function adds it back

        Args:
            node: UIConnectorNode - the current node we are analysing (as the function is recursive this changes in every
            stack frame)
            path: list - this stores how far down the path the function is, also informing it when to stop
            data: str - the data that needs to be added
            data_type: Types - the data type of the data being added
            full_path: str - the full path this addition needs

        Note:
            While it is similar to the recursive addition in the path screen, this has slightly different data that we
            have hence we can make it slightly simpler
        """
        if len(path) > 1:
            path_bit_already_exists = False
            for child in node.children:
                if child.label.plain == path[0]:
                    path_bit_already_exists = True
                    del path[0]
                    self.recursive_addition(child, path, data, data_type, full_path)
            if not path_bit_already_exists:
                new_node = node.add(path[0])
                del path[0]
                self.recursive_addition(new_node, path, data, data_type, full_path)
        else:
            node.add_leaf(path[0] + "=" + data, data={full_path: data, "type": data_type})

    def recursive_searching_for_var(self, node: UIConnectorNode, path: list, variable: str) -> UIVariableNode:
        """Recursively searches for a var so the undo function can do something with it - often deletion

        Args:
            node: UIConnectorNode - the starting node, often the root node
            path: list - storing how deep into the path we are, so we know when it is found
            variable: str - the data in the variable so it can be identified

        Returns:
            UIVariableNode - the found variable node
        """

        if len(path) > 1:
            for child in node.children:
                if child.label.plain == path[0]:
                    del path[0]
                    return self.recursive_searching_for_var(child, path, variable)
        elif len(path) == 1:
            for child in node.children:
                if child.label.plain == path[0] + "=" + variable:
                    return child

    def recursive_searching_for_connector(self, node: UIConnectorNode, path: list) -> UIConnectorNode:
        """Recursively searches for a section so the undo function can add and delete sections

        Args:
            node: UIConnectorNode - the starting node
            path: list - a path to store how close we are and when to stop

        Returns:
            UIConnectorNode - the found connector node
        """
        if len(path) > 1:
            for child in node.children:
                if child.label.plain == path[0]:
                    del path[0]
                    return self.recursive_searching_for_connector(child, path)
        else:
            for child in node.children:
                if child.label.plain == path[0]:
                    return child
            return node.tree.root

    def on_tree_node_selected(self, node: Tree.NodeSelected) -> None:
        """Called when the user selects a node (section or var) and brings up the appropriate screens

        Args:
            node: Tree.NodeSelected - the node the user chose
        """

        def save_section_changes_to_stack(changes_mode: list | None) -> None:
            """Saves the changes to sections to the operations stack and updates the list view

            Args:
                changes_mode: list | None - saves the operations to the stack
            """

            if changes_mode:
                for change in changes_mode:
                    self.__stack.push(ListItem(Label(change), name=change))
                    self.query_one(ListView).insert(0, [self.__stack.peek()])

        def save_change_to_stack(changes_made: str | None) -> None:
            """Saves the changes to variables to the operations stack and updates the list view

            Args:
                changes_made: str | None - the change made
            """

            if changes_made:
                self.__stack.push(ListItem(Label(changes_made), name=changes_made))
                self.query_one(ListView).insert(0, [self.__stack.peek()])

        if node.node.allow_expand:
            self.app.push_screen(SectionOptionsScreen(node, self.__options), save_section_changes_to_stack)
        else:
            self.app.push_screen(OptionsScreen(node), save_change_to_stack)

    def compose(self) -> ComposeResult:
        """Defines what the main app screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """
        tree: Tree[dict] = Tree(self.__file_name)
        tree.root.expand()
        self.__decomposer.get_tree().add_to_ui(self.__decomposer.get_tree().get_root(), tree.root)
        generations = self.setup_generations()

        with TabbedContent():
            with TabPane(title="tree"):
                yield tree
            with TabPane(title="generations"):
                yield generations
            with TabPane(title="operations stack", id="operations_stack_tab"):
                yield ListView(id="operations_stack")
        yield Header(name="Nix tree", show_clock=True, icon=" ")
        yield Footer()

    def get_tree(self):
        return self.query_one(Tree).root


def main():
    """Decomposes the file and adds to the empty add_branch method of the tree class

    Returns:
        None
    """

    tree = DecomposerTree()
    decomposer = Decomposer(file_path=Path("/home/max/nea/NEA/configuration.nix"), tree=tree)
    # decomposer.get_tree().quick_display(decomposer.get_tree().get_root())
    ui = UI("/home/max/nea/NEA/configuration.nix", decomposer)
    ui.run()


if __name__ == "__main__":
    main()
