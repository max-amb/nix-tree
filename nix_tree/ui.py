"""Ui"""

import subprocess
from pathlib import Path
from time import sleep

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import Label, ListView, ListItem, OptionList, Tree, Header, Footer, TabbedContent, \
    TabPane, Button

from nix_tree.composer import Composer
from nix_tree.custom_types import UIVariableNode, UIConnectorNode
from nix_tree.decomposer import DecomposerTree, Decomposer
from nix_tree.errors import CrazyError, NodeNotFound
from nix_tree.help_screens import MainHelpScreen
from nix_tree.parsing import ParsingOptions, Types
from nix_tree.stacks import OperationsStack, OperationsQueue
from nix_tree.tree import VariableNode, ConnectorNode, Node
from nix_tree.variable_screens import OptionsScreen
from nix_tree.section_screens import SectionOptionsScreen

class QueueScreen(ModalScreen[bool]):
    """The screen where the user can choose to apply their changes to the file or not"""

    BINDINGS = [
        ("escape", "quit_pressed")
    ]

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

        with Vertical(id="apply_queue"):
            with Center():
                yield ListView(*self.__queue_as_list, id="operations_list_queue")
                with Center():
                    with Horizontal(id="buttons"):
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

    def action_quit_pressed(self) -> None:
        """Quits the screen when the esc is pressed"""

        self.dismiss(False)


class HomeManagerGenerationScreen(ModalScreen[list[str]]):
    """The screen brought up if the user chooses to select a home-manager generation"""

    BINDINGS = [
        ("escape", "quit_pressed")
    ]

    def __init__(self, title: str):
        """Redefining the init function to take in the home-manager generation as an argument

        Args:
            title: str - the home manager generation
        """

        self.__title = title
        super().__init__()

    def on_button_pressed(self, choice: Button.Pressed):
        """Called when one of the buttons are pressed completing what the user has selected

        Args:
            choice: Button.Pressed - contains which button was pressed
        """

        match choice.button.id:
            case "activate":
                self.dismiss(f"{self.__title.split()[-1]}/activate".split())
            case "remove":
                self.dismiss(f"home-manager remove-generations {self.__title.split()[4]}".split())

    def compose(self) -> ComposeResult:
        """Defines what the home-manager screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        with Vertical(id="generation_options"):
            with Horizontal(id="generation_text"):
                yield Label(f"Date built: {self.__title.split()[0]}   ")
                yield Label(f"Id: {self.__title.split()[4]}")
            with Horizontal(id="buttons"):
                yield Button(label="Activate", variant="success", id="activate")
                yield Button(label="Remove", variant="error", id="remove")

    def action_quit_pressed(self) -> None:
        """Quits the screen when the esc is pressed"""

        self.app.pop_screen()


class UI(App[list[str]]):
    """Defines the main screen of the app"""

    CSS_PATH = "css.css"  # The path to the CSS to decorate the UI

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

        # This allows for the program to run without a constant options location
        # It was an issue as it wouldn't allow the program to be installed without hardcoding
        # the options location.
        path_of_executable = Path(__file__).parts
        options_location = Path()
        if 'store' in path_of_executable: # If it is being run as a flake
            for i in path_of_executable:
                if i == "lib":
                    break
                options_location = options_location / i
            options_location = options_location / "data/options.json"
        else: # If it is not being run as a flake
            for i in path_of_executable:
                if i == "nix_tree":
                    options_location = options_location / i
                    break
                options_location = options_location / i
            options_location = options_location / "data/options.json"

        self.__options = ParsingOptions(options_location)
        self.__file_name = file_name
        self.__decomposer = decomposer
        super().__init__()

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
                        node_to_delete: UIVariableNode | None = self.recursive_searching_for_var(
                            self.query_one(Tree).root,
                            path.split("."),
                            variable
                        )
                        if node_to_delete:
                            node_to_delete.remove()
                        else:
                            raise NodeNotFound(node_name=full_path)
                    case "Change":
                        change_command: str = action[7:]  # Can't use space splits as it changes the lists spaces
                        pre: list = change_command.split("->")[0].strip().split("=")
                        post: list = change_command.split("->")[1].strip().split("=")
                        variable_to_change: UIVariableNode | None = self.recursive_searching_for_var(
                            self.query_one(Tree).root,
                            post[0].split("."),
                            post[1]
                        )
                        if variable_to_change:
                            new_label = f"{pre[0].split('.')[-1]}={pre[1]}"
                            variable_to_change.label = new_label
                            if variable_to_change.data:
                                variable_to_change.data[post[0]] = pre[1]
                            else:
                                raise NodeNotFound(node_name='='.join(post))
                        else:
                            raise NodeNotFound(node_name='='.join(post))
                    case "Section":
                        match action.split(" ")[-1]:
                            case "deleted":
                                path_as_list = action.split(" ")[1].split(".")
                                if len(path_as_list) > 1:
                                    path_before_section = path_as_list[:-1]
                                else:
                                    path_before_section = path_as_list
                                section_node: UIConnectorNode | None = self.recursive_searching_for_connector(
                                    self.query_one(Tree).root,
                                    path_before_section
                                )
                                if section_node:
                                    section_node.add(path_as_list[-1], after=0)
                                else:
                                    raise NodeNotFound(node_name='.'.join(path_as_list))
                            case "added":
                                path_as_list = action.split(" ")[1].split(".")
                                section_node: UIConnectorNode | None = self.recursive_searching_for_connector(
                                    self.query_one(Tree).root,
                                    path_as_list
                                )
                                if section_node:
                                    section_node.remove()
                                else:
                                    raise NodeNotFound(node_name='.'.join(path_as_list))
        else:
            self.notify("The operations stack is empty")

    def __remove_empty_sections(self, node: UIConnectorNode, operations: list[str]) -> list[str]:
        if node.children:
            for child in node.children:
                print(child.label)
                operations = self.__remove_empty_sections(child, operations)
        elif "=" not in node.label:
            node.remove()
            operations.append(f"Section {node.label} deleted")
            return operations
        return operations

    def __apply_changes(self) -> None:
        """Applies the changes stored in the operations queue to the decomposer tree for changing the file"""

        tree: DecomposerTree = self.__decomposer.get_tree()
        while self.__queue.get_len() > 0:
            action = self.__queue.dequeue().name
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
                    case "Added":
                        tree.add_branch(full_path)
                    case "Delete":
                        parent: Node | None = tree.find_node_parent(full_path, tree.get_root())
                        if parent:
                            if isinstance(parent, ConnectorNode):
                                parent.remove_child_variable_node(full_path)
                            else:
                                raise NodeNotFound(node_name=full_path)
                        else:
                            raise NodeNotFound(node_name=full_path)
                    case "Change":
                        change_command: str = action[7:]
                        pre: str = change_command.split("->")[0].strip()
                        post: str = change_command.split("->")[1].strip()
                        node_to_edit: Node = tree.find_variable_node(pre, tree.get_root())
                        if isinstance(node_to_edit, VariableNode):
                            node_to_edit.set_data(post.split("=")[1])
                        else:
                            raise NodeNotFound(node_name=full_path)
                    case "Section":
                        match action.split(" ")[-1]:
                            case "deleted":
                                parent: Node | None = tree.find_section_node_parent(action.split(" ")[1], tree.get_root())
                                if parent:
                                    if isinstance(parent, ConnectorNode):
                                        parent.remove_child_section_node(action.split(" ")[1].split(".")[-1])
                                    else:
                                        raise NodeNotFound(node_name=action.split(" ")[1])
                                else:
                                    raise NodeNotFound(node_name=action.split(" ")[1])
                            case "added":
                                parent: Node | None = tree.find_section_node_parent(action.split(" ")[1], tree.get_root())
                                if parent:
                                    if isinstance(parent, ConnectorNode):
                                        parent.add_node(ConnectorNode(action.split(" ")[1].split(".")[-1]))
                                    else:
                                        raise NodeNotFound(node_name=action.split(" ")[1])
                                else:
                                    raise NodeNotFound(node_name=action.split(" ")[1])

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
                queue_as_strings = []
                for item in saved_queue:
                    queue_as_strings.append(item.name)
                self.app.exit(queue_as_strings)
            else:
                while self.__queue.get_len() > 0:
                    self.__stack.push(self.__queue.dequeue())

        commands = self.__remove_empty_sections(self.app.query_one(Tree).root, [])
        if commands:
            for command in commands:
                self.__stack.push(ListItem(Label(command), name=command))
                self.query_one(ListView).insert(0, [self.__stack.peek()])
        while self.__stack.get_len() > 0:
            self.__queue.enqueue(self.__stack.pop())
        saved_queue = self.__queue.return_queue()[:]
        self.app.push_screen(QueueScreen(self.__queue.return_queue()), handle_response_from_queue_screen)

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

    def recursive_searching_for_var(self, node: UIConnectorNode, path: list, variable: str) -> UIVariableNode | None:
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
                if str(child.label) == path[0]:
                    del path[0]
                    return self.recursive_searching_for_var(child, path, variable)
        elif len(path) == 1:
            for child in node.children:
                if str(child.label) == path[0] + "=" + variable:
                    return child

    def recursive_searching_for_connector(self, node: UIConnectorNode, path: list) -> UIConnectorNode | None:
        """Recursively searches for a section so the undo function can add and delete sections

        Args:
            node: UIConnectorNode - the starting node
            path: list - a path to store how close we are and when to stop

        Returns:
            UIConnectorNode - the found connector node
        """
        if len(path) > 1:
            for child in node.children:
                if str(child.label) == path[0]:
                    del path[0]
                    return self.recursive_searching_for_connector(child, path)
        else:
            for child in node.children:
                if str(child.label) == path[0]:
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

    def on_option_list_option_selected(self, choice: OptionList.OptionSelected) -> None:
        """Opened if the user chooses an option - usually in generation management

        Args:
            choice: OptionList.OptionSelected - the option the user chose
        """

        def handle_home_manager_choice(cmd: list[str] | None):
            """If the user chose to do something with home-manager, this gets called

            Args:
                cmd: list[str] | None - the users choice (None if they chose nothing)
            """

            self.app.exit(cmd)

        if choice.option_list.id in ("system-switch-options", "home-manager-gens"):
            match choice.option.prompt:
                case "switch":
                    self.app.exit("sudo nixos-rebuild switch".split())
                case "boot":
                    self.app.exit("sudo nixos-rebuild boot".split())
                case "test":
                    self.app.exit("sudo nixos-rebuild test".split())
                case "dry-activate":
                    self.app.exit("sudo nixos-rebuild dry-activate".split())
                case "build-vm":
                    self.app.exit("sudo nixos-rebuild build-vm".split())
                case _:  # Home-manager
                    self.app.push_screen(HomeManagerGenerationScreen(str(choice.option.prompt)), handle_home_manager_choice)

    def on_button_pressed(self, choice: Button.Pressed):
        """Called if a button is pressed - only really in generation management

        Args:
            choice: Button.Pressed - the users choice
        """

        match choice.button.id:
            case "switch_hm":
                self.app.exit("home-manager switch".split())
            case "build_hm":
                self.app.exit("home-manager build".split())

    def compose(self) -> ComposeResult:
        """Defines what the main app screen will look like

        Returns:
            ComposeResult - the screen in a form the library understands
        """

        tree: Tree[dict] = Tree(self.__file_name)
        tree.root.expand()
        self.__decomposer.get_tree().add_to_ui(self.__decomposer.get_tree().get_root(), tree.root)

        with TabbedContent():
            with TabPane(title="tree"):
                yield tree
            with TabPane(title="generations"):
                with TabbedContent():
                    with TabPane(title="System"):
                        yield OptionList(
                            "switch",
                            "boot",
                            "test",
                            "build",
                            "dry-activate",
                            "build-vm",
                            id="system-build-options"
                        )
                    with TabPane(title="Home Manager"):
                        generation_command = subprocess.run("home-manager generations".split(), capture_output=True,
                                                            text=True, check=True)
                        yield OptionList(*generation_command.stdout.split("\n")[:-1], id="home-manager-gens")
                        with Horizontal(id="buttons"):
                            yield Button(label="switch", variant="success", id="switch_hm")
                            yield Button(label="build", id="build_hm")
            with TabPane(title="operations stack", id="operations_stack_tab"):
                yield ListView(id="operations_stack")
        yield Header(name="Nix tree", show_clock=True, icon=" ")
        yield Footer()


def start_ui(file_location: str, write_over: bool, comments: bool) -> None:
    """Makes a DecomposerTree object along with calling the decomposer object to fill the tree, it then passes it into
    the ui object from which it runs the ui"""

    tree = DecomposerTree()
    decomposer = Decomposer(file_path=Path(file_location), tree=tree)
    ui = UI(file_location, decomposer)
    command: list[str] | None = ui.run()
    if command:
        # If command is an actual command it will be executed, otherwise it is a list of operations for the composer to use in the edit the file option
        if any(substring in ' '.join(command) for substring in ["sudo", "home-manager", "activate"]):
            subprocess.run(command, check=True)  # To error out if the command fails
            sleep(5)
            start_ui(file_location, write_over, comments)
        else:
            Composer(decomposer.get_tree(), file_location, write_over, comments)
