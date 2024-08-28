"""Contains the tree implementation"""
from custom_types import UIConnectorNode
from parsing import Types
from errors import CrazyError, NodeNotFound


def find_type(variable: str) -> Types:
    """Works out the type of the variable passed in

    Args:
        variable: str - The variable passed in to be checked

    Returns:
        Types - The variable type

    Note:
        The organisation of these if clauses is important, if the string one is before the list one then any list of
        strings would get classified as a string
    """

    if variable.isdigit():
        return Types.INT
    if variable in ("true", "false"):
        return Types.BOOL
    if "[" in variable:
        return Types.LIST
    if "'" in variable:
        return Types.STRING
    return Types.UNIQUE


class Node:
    """The base Node class which the other node classes inherit from"""

    def __init__(self, name: str) -> None:
        """Sets the name of the node
        
        Args:
            name: str - the name to be set
        """

        self.__name = name
        self.__comments = None

    def get_name(self) -> str:
        """Returns the nodes name

        Returns:
            str - the Nodes name
        """

        return self.__name

    def set_name(self, new_name: str) -> None:
        """Allows the nodes name to be set if required

        Args:
            new_name: str - the name to be changed to/the new name
        """

        self.__name = new_name

    def get_connected_nodes(self) -> list:
        """Default get connected nodes method, connector nodes override it

        Returns:
            list - an empty list (returned for variables)
        """
        return []

    def set_comments(self, comments: list[str]) -> None:
        self.__comments = comments

    def get_comments(self) -> list[str]:
        return self.__comments

class ConnectorNode(Node):
    """The connector node, it is a part of the path

    Note:
        A connector nodes name is simply what section of the path it refers to, e.g. services
        not the full path
    """

    def __init__(self, name: str) -> None:
        """Sets the name of the node and initialises its children list

        Args:
            name: str - the name to be set
        """

        super().__init__(name)
        self.__children: list[Node] = []

    def add_node(self, node: Node) -> None:
        """Adds a new node to the children of the connector node

        Args:
            node: Node - the node to be added
        """

        self.__children.append(node)

    def get_connected_nodes(self) -> list[Node]:
        """Returns the list of connected nodes

        Returns:
            list[Node] - the children list
        """

        return self.__children

    def remove_child_variable_node(self, full_path: str) -> None:
        for i, node in enumerate(self.__children):
            if isinstance(node, VariableNode):
                if node.get_name() + "=" + node.get_data() == full_path:
                    self.__children.pop(i)
                    return
        raise NodeNotFound(full_path)

    def remove_child_section_node(self, name: str) -> None:
        for i, node in enumerate(self.__children):
            if isinstance(node, ConnectorNode):
                if node.get_name() == name:
                    self.__children.pop(i)
                    return
        raise NodeNotFound(name)


class VariableNode(Node):
    """The variable node, it stores a value such as true or 'vim'

    Note:
        A variable nodes name will always be its full path, e.g. programs.firefox.enable
        The lack of a setter for data_type is intentional as these will never need to be changed
    """

    def __init__(self, name: str, data, data_type: Types) -> None:
        """Sets the name of the node, its data and that datas type and if it is part of a list

        Args:
            name: str - the name to be set
            data: unknown - the data for the variable
            data_type: Types - the type of the data the variable stores
        """

        super().__init__(name)
        self.__type = data_type
        self.__data = data

    def get_type(self) -> Types:
        """Returns the data type of the variable 

        Returns:
            Types - the data type of the variable
        """

        return self.__type

    def get_data(self):
        """Returns the data stored in the variable

        Returns:
            unknown: the data
        """

        return self.__data

    def set_data(self, data) -> bool:
        """Sets the data within the variable

        Args:
            data: unknown - the new data to put in the variable

        Returns:
            bool - true if the operation was successful false if not
        """

        if self.__type == find_type(data):
            self.__data = data
            return True
        return False


class DecomposerTree:
    """An implementation of a rooted tree

    Note:
        https://computersciencewiki.org/index.php/Tree#Standards
    """

    def __init__(self) -> None:
        """Creates the root node from which all other nodes will be connected to"""
        self.__root_node = ConnectorNode("")

    def get_root(self) -> ConnectorNode:
        """Returns the root node if something needs to traverse the tree

        Returns:
            ConnectorNode - the root node
        """

        return self.__root_node

    def add_branch(self, contents: str) -> None:
        """Adds a variable to the tree, creating the path out of connector nodes as required

        Args:
            contents: str - the variables full path
        """

        string_path, variable = (contents.split("=")[0], contents.split("=")[1])
        path = string_path.split(".")
        found_node = self.find_variable_node(contents, self.__root_node)
        if isinstance(found_node, VariableNode):
            print("Node already in tree")
        elif isinstance(found_node, ConnectorNode):
            node_path = found_node.get_name()
            if not node_path == "":
                path = path[path.index(node_path) + 1:]
            nodes: list[ConnectorNode] = [found_node]
            for bit_of_path_itr in range(len(path) - 1):
                nodes.append(ConnectorNode(path[bit_of_path_itr]))
            for node_itr in range(len(nodes) - 1):
                nodes[node_itr].add_node(nodes[node_itr + 1])
            nodes[len(nodes) - 1].add_node(VariableNode(string_path, variable, find_type(variable)))

    def find_variable_node(self, path: str, node: Node, covered_path=None) -> Node:
        """Recursively searches the tree looking for a node

        Args:
            path: str - the path of the variable it is looking for
            node: Node - the node to search from on this recursion - usually the root node
            covered_path: None(list) - how much of the path has been covered (used for recursion)

        Returns:
            Node - the node found, if it is a variable then it is the precise node that was being searched
            for but if it is a connector node it is the closest it got to the variable
        """

        if isinstance(node, VariableNode) or covered_path == []:
            return node
        if isinstance(node, ConnectorNode):
            if covered_path is None:
                covered_path = path.split("=")[0].split(".")

            node_to_visit: str = covered_path[0]

            for i in node.get_connected_nodes():
                if isinstance(i, ConnectorNode):
                    if node_to_visit == i.get_name():
                        del covered_path[0]
                        return self.find_variable_node(path, i, covered_path)
                elif isinstance(i, VariableNode):
                    if path.split("=")[0] == i.get_name():
                        return i
            return node
        raise CrazyError()

    def find_node_parent(self, path: str, node: Node, covered_path=None) -> Node:
        if covered_path is None:
            path = path.split("=")[0]
            covered_path = path.split(".")
        if len(covered_path) > 1:
            node_to_visit: str = covered_path[0]
            for nodes in node.get_connected_nodes():
                if node_to_visit == nodes.get_name():
                    del covered_path[0]
                    return self.find_node_parent(path, nodes, covered_path)
        else:
            return node

    def find_section_node_parent(self, path: str, node: Node, covered_path=None) -> Node:
        if covered_path is None:
            covered_path = path.split(".")
        if len(covered_path) > 1:
            node_to_visit: str = covered_path[0]
            for nodes in node.get_connected_nodes():
                if node_to_visit == nodes.get_name():
                    del covered_path[0]
                    return self.find_node_parent(path, nodes, covered_path)
        else:
            return node

    def quick_display(self, node: Node, append: str = "") -> None:
        """Recursively displays the tree on the console

        Args:
            node: Node - the node to start displaying from - usually the root node
            append: str - to store how deep in the indentation we are
        """

        if isinstance(node, ConnectorNode):
            print(append + node.get_name())
            for i in node.get_connected_nodes():
                self.quick_display(i, append + "  ")
        if isinstance(node, VariableNode):
            print(append + "|--" + node.get_name().split(".")[-1] + "=" + node.get_data())

    def add_to_ui(self, node: Node, previous_node: UIConnectorNode) -> None:
        """Iterates through the tree adding nodes to the ui tree

        Args:
            node: Node - the node to start displaying from - usually the root node
            previous_node: UIConnectorNode - initially the root node, stores where you are in the tree

        Note:
            The avoidance of adding the root node to the ui tree means that there isn't a blank space to represent the
            root node of the decomposer tree.
        """

        if isinstance(node, ConnectorNode):
            children = node.get_connected_nodes()
            if node != self.get_root():
                prev_node = previous_node.add(node.get_name())
            else:
                prev_node = previous_node
            for child in children:
                self.add_to_ui(child, prev_node)
        if isinstance(node, VariableNode):
            if len(node.get_name().split(".")) > 1:
                label = node.get_name().split(".")[-1] + "=" + node.get_data()
            else:
                label = node.get_name() + "=" + node.get_data()
            previous_node.add_leaf(str(label), data={node.get_name(): node.get_data(), "type": node.get_type()})
