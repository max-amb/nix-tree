"""The section management screens, such as adding a var or section or deleting a section"""

import re

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import Input, Label, OptionList, Tree, Button, RadioSet

from nix_tree.custom_types import UIConnectorNode
from nix_tree.help_screens import SectionOptionsHelpScreen
from nix_tree.parsing import ParsingOptions, Types


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
        path.insert(0, str(current_node.label))
        if current_node.parent:  # Every node will have a parent but the root node - this is just for pylint
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

        clean_input: str = re.sub(r"(\[)(\s*)", "[ ", user_input.value)
        clean_input: str = re.sub(r"(\s*)(\])", " ]", clean_input)
        self.dismiss(clean_input)


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
                elif data[1] == Types.STRING and (not re.search(r"\A'.+'\Z", data[0])):
                    self.notify("You lost a speech mark! Not updating")
                    if type_as_defined:
                        self.app.push_screen(RecommendedTypeOrChooseType(type_as_defined),
                                             handle_return_from_variable_addition)
                    else:
                        self.app.push_screen(AddScreenVariableSelection(), handle_return_from_variable_addition)
                else:
                    path_as_list = work_out_full_path(self.__node.node, [])
                    if data[1]:
                        node_added = self.recursive_addition(self.__node.node, path.value.split("."), data[0], path_as_list,
                                                         data[1])
                    else:
                        raise TypeError("The nodes type could not be determined")
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
                           data_type: Types) -> bool | None:
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
        return None

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
            recommended_type: tuple[Types, str] - the type that has been found
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
