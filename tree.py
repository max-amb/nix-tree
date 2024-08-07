"""Contains the tree implementation"""
from enum import Enum


class Types(Enum):
    """This enum defines the possible types for nix variables"""
    BOOL = 0
    INT = 1
    STRING = 2
    UNIQUE = 3


def find_type(variable: str) -> Types:
    """Works out the type of the variable passed in

    Args:
        variable: str - The variable passed in to be checked

    Returns:
        Types - The variable type
    """

    if variable.isdigit():
        return Types.INT
    if variable in ("true", "false"):
        return Types.BOOL
    if "\"" in variable:
        return Types.STRING
    return Types.UNIQUE


class NodeNotFound(Exception):
    """Raised when the node does not exist in the tree

    Args:
        node_name: str - the name of the node that does not exist in the tree
        message: str - the message to print out with this exception

    Note:
        https://www.programiz.com/python-programming/user-defined-exception
    """

    def __init__(self, node_name: str, message: str = "Node {NODE} does not exist in the tree"):
        super().__init__(message.format(NODE=node_name))


class CrazyError(Exception):
    """Raised when I have no idea what has happened, should never be raised

    Args:
        message: str - the message to print out with this exception

    Note:
        https://www.programiz.com/python-programming/user-defined-exception
    """

    def __init__(self, message: str = "How on gods green earth did you get here"):
        super().__init__(message)


class Node:
    """The base Node class which the other node classes inherit from"""

    def __init__(self, name: str) -> None:
        """Sets the name of the node
        
        Args:
            name: str - the name to be set
        """

        self.__name = name

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


class VariableNode(Node):
    """The variable node, it stores a value such as true or 'vim'

    Note:
        A variable nodes name will always be its full path, e.g. programs.firefox.enable=true
        The lack of setters for data_type and is_list is intentional as these will never need to be changed
    """

    def __init__(self, name: str, data, data_type: Types, is_list: bool) -> None:
        """Sets the name of the node, its data and that datas type and if it is part of a list

        Args:
            name: str - the name to be set
            data: unknown - the data for the variable
            data_type: Types - the type of the data the variable stores
            is_list: bool - Whether the variable is part of a list
        """

        super().__init__(name)
        self.__type = data_type
        self.__data = data
        self.__is_list = is_list

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

    def is_list(self) -> bool:
        """Returns whether the variable is part of a list

        Returns:
            bool: true if the variable is part of a list
        """

        return self.__is_list

    def set_data(self, data) -> bool:
        """Sets the data within the variable

        Args:
            data: unknown - the new data to put in the variable

        Returns:
            bool - true if the operation was successful false if not
        """

        if self.__type == find_type(data):
            self.__data = data
            old_name: str = self.get_name()
            new_name = old_name.split("=")[0] + data
            self.set_name(new_name)
            return True
        return False


class Tree:
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

    def add_branch(self, contents: str, is_list: bool) -> None:
        """Adds a variable to the tree, creating the path out of connector nodes as required

        Args:
            contents: str - the variables full path
            is_list: bool - true if the variable is part of a list and false if not
        """

        string_path, variable = (contents.split("=")[0], contents.split("=")[1])
        path = string_path.split(".")
        found_node = self.find_node(contents, self.__root_node)
        if isinstance(found_node, VariableNode):
            print("Node already in tree")
        elif isinstance(found_node, ConnectorNode):
            node_path = found_node.get_name()
            if not node_path == "":
                path = path[path.index(node_path)+1:]
            nodes: list[ConnectorNode] = [found_node]
            for bit_of_path in path:
                nodes.append(ConnectorNode(bit_of_path))
            for node_itr in range(len(nodes)-1):
                nodes[node_itr].add_node(nodes[node_itr+1])
            nodes[len(nodes)-1].add_node(VariableNode(string_path, variable, find_type(variable), is_list))

    def find_node(self, path: str, node: Node, covered_path=None) -> Node:
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
                path = path.split("=")[0]
                covered_path = path.split(".")

            node_to_visit: str = covered_path[0]

            for i in node.get_connected_nodes():
                if node_to_visit == i.get_name():
                    del covered_path[0]
                    node = self.find_node(path, i, covered_path)
                    return node
            return node
        raise CrazyError()

    def quick_display(self, node: Node, append: str = "") -> None:
        """Recursively displays the tree on the console

        Args:
            node: Node - the node to start displaying from - usually the root node
            append: str - to store how deep in the indentation we are
        """

        if isinstance(node, ConnectorNode):
            print(append+node.get_name())
            for i in node.get_connected_nodes():
                self.quick_display(i, append+"  ")
        if isinstance(node, VariableNode):
            print(append+"|--"+node.get_data()+" "+str(node.is_list()))
