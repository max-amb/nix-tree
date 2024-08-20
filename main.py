"""Ui tests"""
from errors import CrazyError, NoValidHeadersNode
from parsing import ParsingOptions, Types
from decomposer import DecomposerTree, Decomposer
from tree import VariableNode, ConnectorNode, Node
from help_screens import MainHelpScreen, OptionsHelpScreen, SectionOptionsHelpScreen
from custom_types import UIVariableNode, UIConnectorNode
from stacks import OperationsStack, OperationsQueue

from pathlib import Path
import re
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import Input, Label, ListView, ListItem, OptionList, Tree, Header, Footer, TabbedContent, \
    TabPane, Button, RadioSet

OPTIONS_LOCATION: str = "/home/max/options.json"
FILE_LOCATION: str = "/home/max/nea/NEA/configuration.nix"


class ComposerIterator:
    prepend: str = ""
    previous_prepend: str = ""
    lines: str = ""


class Composer:
    def __init__(self, decomposer: Decomposer):
        self.__tree: DecomposerTree = decomposer.get_tree()
        self.__comments: dict[str, str] = decomposer.get_comments_attached_to_line()
        self.__file_location = FILE_LOCATION + ".new"
        self.__composer_iterator = ComposerIterator()
        self.write_to_file()

    def write_to_file(self):
        self.__separate_and_add_headers()
        self.__work_out_lines(self.__tree.get_root())
        with open(self.__file_location, "w") as file:
            file.write(self.__composer_iterator.lines)

    def __work_out_lines(self, node: Node) -> None:
        if isinstance(node, ConnectorNode):
            if len(node.get_connected_nodes()) > 1:
                if self.__composer_iterator.lines[-1] != ":":
                    if self.__composer_iterator.lines[-1] == ".":
                        self.__composer_iterator.lines += node.get_name() + " = {\n"
                    elif self.__composer_iterator.lines[-1] == "\n":
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + " = {\n"
                    else:
                        raise CrazyError
                else:
                    self.__composer_iterator.lines += "\n\n{\n"
                self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend
                self.__composer_iterator.prepend += "  "
                for singular_node in node.get_connected_nodes():
                    self.__work_out_lines(singular_node)
                if self.__composer_iterator.previous_prepend != "":
                    self.__composer_iterator.lines += self.__composer_iterator.previous_prepend + "};\n"
                else:  # Then it is the end of the file
                    self.__composer_iterator.lines += self.__composer_iterator.previous_prepend + "}\n"
                self.__composer_iterator.prepend = self.__composer_iterator.previous_prepend
                self.__composer_iterator.previous_prepend = self.__composer_iterator.previous_prepend[2:]
                if len(self.__composer_iterator.prepend) == 2:
                    self.__composer_iterator.lines += "\n"
            elif len(node.get_connected_nodes()) == 1:
                if self.__composer_iterator.lines[-1] == ".":
                    self.__composer_iterator.lines += node.get_name() + "."
                elif self.__composer_iterator.lines[-1] == "\n":
                    self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + "."
                else:
                    raise CrazyError
                self.__work_out_lines(node.get_connected_nodes()[0])
            else:
                pass
        elif isinstance(node, VariableNode):
            data = node.get_name().split(".")[-1] + " = "

            if node.get_type() == Types.LIST:
                if "'" not in node.get_data():
                    data_as_list = node.get_data().split(" ")
                    data_as_list = data_as_list[1:-1]
                    if len(data_as_list) >= 3:
                        data += "[\n"
                        for list_item in data_as_list:
                            data += self.__composer_iterator.prepend + "  " + list_item + "\n"
                        data += self.__composer_iterator.prepend + "]"
                    else:
                        data += node.get_data()
                else:
                    data_as_list = node.get_data().split("' '")
                    data_as_list = data_as_list[1:-1]
                    if len(data_as_list) >= 3:
                        data += "[\n"
                        for list_item in data_as_list:
                            data += self.__composer_iterator.prepend + "  '" + list_item + "'\n"
                        data += self.__composer_iterator.prepend + "]"
                    else:
                        data += node.get_data()
            else:
                data += node.get_data()

            #  to change ' back into "
            data = re.sub("'", "\"", data)

            if node.get_type() == Types.LIST and "(" in data:  # needs to be handled with a with clause
                with_clause = data[data.index("(") + 1:data.index(")")]
                data = re.sub(rf"\({with_clause}\)\.", "", data)
                data = data.split("=")[0] + "= with " + with_clause + ";" + data.split("=")[1]

            if self.__composer_iterator.lines[-1] == ".":
                self.__composer_iterator.lines += data + ";\n"
            elif self.__composer_iterator.lines[-1] == "\n":
                self.__composer_iterator.lines += self.__composer_iterator.prepend + data + ";\n"
            else:
                raise CrazyError

    def __separate_and_add_headers(self) -> None:
        headers_node = None
        for singular_node in self.__tree.get_root().get_connected_nodes():
            if singular_node.get_name() == "headers":
                headers_node = singular_node
        if isinstance(headers_node, VariableNode):
            headers: str = headers_node.get_data()
            headers = re.sub(r"\[|]", "", headers)
            headers_as_list = headers.split(", ")
            if len(headers_as_list) >= 4:
                self.__composer_iterator.lines += "{ "
                for header in headers_as_list:
                    if header != headers_as_list[-1]:  # to avoid putting a comma on the final header
                        self.__composer_iterator.lines += header.strip() + ",\n"
                    else:
                        self.__composer_iterator.lines += header.strip() + "\n"
                self.__composer_iterator.lines += "}:"
            else:
                self.__composer_iterator.lines += "{" + headers + "}:"
            self.__tree.get_root().remove_child_variable_node(headers_node.get_name() + "=" + headers_node.get_data())
        else:
            raise NoValidHeadersNode


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
                self.__node.node.label = self.__path.split(".")[-1] + "=" + new_data.value.replace("[", "[ ")
                if self.__node.node.data:
                    self.__node.node.data[self.__path] = new_data.value.replace("[", "[ ")
                self.dismiss(f"Change {self.__path}={self.__value.replace("[", "[ ")} -> "
                             f"{self.__path}={new_data.value.replace("[", "[ ")}")
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

        self.dismiss(user_input.value.replace("[", "[ "))
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
        self.__path = ""
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
            node: UIConnectorNode - the current node we are analysing (as the function is recursive this changes in
            every stack frame)
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


class QueueScreen(ModalScreen[bool]):
    """The screen where the user can choose to apply their changes to the file or not"""

    def __init__(self, queue: list) -> None:
        """Redefining the init function to take in a queue list for displaying in the ListView

        Args:
            queue: list - the queue as a list
        """

        self.__queue_as_list = []
        for item in queue:
            self.__queue_as_list.append(ListItem(Label(item.name), name=item.name))
        super().__init__()

    def compose(self) -> ComposeResult:
        """Defines what the queue screen will look like (e.g. for adding a section)

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Vertical():
            with Center():
                yield ListView(*self.__queue_as_list, id="operations_list_queue")
                with Horizontal():
                    yield Button("Apply", id="apply", variant="success")
                    yield Button("Don't apply", id="do_not_apply", variant="error")

    def on_button_pressed(self, button: Button.Pressed) -> None:
        """Called when the user chooses one of the buttons, the function removes its screen returning true if the
        user chose to apply and false if not

        Args:
            button: Button.Pressed - an object detailing which button was clicked
        """

        if button.button.id == "apply":
            self.dismiss(True)
        else:
            self.dismiss(False)


class UI(App):
    """Defines the main screen of the app"""

    """The path to the css"""
    CSS_PATH = "css.css"

    BINDINGS = [
        ("q", "quit", "To quit the app"),
        ("?", "help", "Show help screen"),
        ("u", "undo", "To undo the previous change"),
        ("e", "empty", "To empty the operations stack"),
        ("a", "apply", "To apply your changes to the file"),
    ]

    def __init__(self, file_name: str, decomposer: Decomposer) -> None:
        """Redefining the init function to initialise two objects, the stack and the options parser,
        it also takes in the file name to place as the title of the tree

        Args:
            file_name: str - the file name
            decomposer: Decomposer - a decomposer object to form the tree
        """

        self.__stack = OperationsStack()
        self.__queue = OperationsQueue()
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
                            raise TypeError("Cannot deduce node variable type")
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
                                section_node.add(path_as_list[-1], after=0)
                            case "added":
                                path_as_list = action.split(" ")[1].split(".")
                                section_node: UIConnectorNode = self.recursive_searching_for_connector(
                                    self.query_one(Tree).root,
                                    path_as_list
                                )
                                section_node.remove()
        else:
            self.notify("The operations stack is empty")

    def __apply_changes(self) -> None:
        """Applies the changes stored in the operations queue to the decomposer tree for changing the file"""

        tree: DecomposerTree = self.__decomposer.get_tree()
        while self.__queue.get_len() > 0:
            action = self.__queue.dequeue().name
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
                case "Added":
                    tree.add_branch(full_path)
                case "Delete":
                    parent: Node = tree.find_node_parent(full_path, tree.get_root())
                    if isinstance(parent, ConnectorNode):
                        parent.remove_child_variable_node(full_path)
                    else:
                        raise CrazyError
                case "Change":
                    change_command: str = action[7:]
                    pre: str = change_command.split("->")[0].strip()
                    post: str = change_command.split("->")[1].strip()
                    node_to_edit: Node = tree.find_variable_node(pre, tree.get_root())
                    if isinstance(node_to_edit, VariableNode):
                        node_to_edit.set_data(post.split("=")[1])
                    else:
                        raise CrazyError(node_to_edit.get_name())
                case "Section":
                    match action.split(" ")[-1]:
                        case "deleted":
                            parent: Node = tree.find_section_node_parent(action.split(" ")[1], tree.get_root())
                            if isinstance(parent, ConnectorNode):
                                parent.remove_child_section_node(action.split(" ")[1].split(".")[-1])
                            else:
                                raise CrazyError
                        case "added":
                            parent: Node = tree.find_section_node_parent(action.split(" ")[1], tree.get_root())
                            if isinstance(parent, ConnectorNode):
                                parent.add_node(ConnectorNode(action.split(" ")[1].split(".")[-1]))
                            else:
                                raise CrazyError

    def action_apply(self) -> None:
        """Called if "a" is pressed, it pushes the apply screen which allows the user to push their changes to the
        configuration file"""

        def handle_response_from_queue_screen(apply: bool | None) -> None:
            """Takes the response from the apply changes screen and either performs the changes or returns the changes
            back to the operations stack

            Args:
                apply: bool | None - true if the changes should be applied and false if not
            """

            if apply:
                self.__apply_changes()
                self.app.exit()
            else:
                while self.__queue.get_len() > 0:
                    self.__stack.push(self.__queue.dequeue())

        while self.__stack.get_len() > 0:
            self.__queue.enqueue(self.__stack.pop())
        queue_to_be_emptied = self.__queue.return_queue()
        self.app.push_screen(QueueScreen(queue_to_be_emptied), handle_response_from_queue_screen)

    def recursive_addition(self, node: UIConnectorNode, path: list, data: str, data_type: Types,
                           full_path: str) -> None:
        """Called by the undo function - if a node has been deleted this function adds it back

        Args:
            node: UIConnectorNode - the current node we are analysing (as the function is recursive this changes in
            every stack frame)
            path: list - this stores how far down the path the function is, also informing it when to stop
            data: str - the data that needs to be added
            data_type: Types - the data type of the data being added
            full_path: str - the full path this addition needs

        Note:
            While it is similar to the recursive addition in the path screen, this has slightly different data that we
            have hence we can make it slightly simpler - also we do not need to make any sections/groups, so it doesn't
            need that functionality.
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
            node.add_leaf(path[0] + "=" + data, data={full_path: data, "type": data_type}, after=0)

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


def main():
    """Makes a DecomposerTree object along with calling the decomposer object to fill the tree, it then passes it into
    the ui object from which it runs the ui"""

    tree = DecomposerTree()
    decomposer = Decomposer(file_path=Path(FILE_LOCATION), tree=tree)
    ui = UI(FILE_LOCATION, decomposer)
    ui.run()
    Composer(decomposer)


if __name__ == "__main__":
    main()
