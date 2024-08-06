"""Contains the tree implementation"""
from enum import Enum


def find_type(variable: str):
    if variable.isdigit():
        return Types.INT
    elif variable == "true" or variable == "false":
        return Types.BOOL
    elif "\"" in variable:
        return Types.STRING
    else:
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
    """Raised when I have no idea what has happened

    Args:
        message: str - the message to print out with this exception

    Note:
        https://www.programiz.com/python-programming/user-defined-exception
    """

    def __init__(self, message: str = "How on gods green earth did you get here"):
        super().__init__(message)


class Types(Enum):
    BOOL = 0
    INT = 1
    STRING = 2
    LIST = 3
    UNIQUE = 4


class Node:
    def __init__(self, name: str):
        self.__name = name

    def get_name(self) -> str:
        return self.__name

    def set_name(self, new_name: str) -> None:
        self.__name = new_name


class ConnectorNode(Node):
    def __init__(self, name: str):
        super().__init__(name)
        self.__children: list[Node] = []

    def add_node(self, node: Node):
        self.__children.append(node)

    def get_connected_nodes(self):
        return self.__children


class VariableNode(Node):
    def __init__(self, name: str, data, data_type: Types, is_list: bool):
        super().__init__(name)
        self.__type = data_type
        self.__data = data
        self.__is_list = is_list

    def get_type(self):
        return self.__type

    def get_data(self):
        return self.__data

    def set_data(self, data):
        if self.__type == find_type(data):
            self.__data = data
            old_name: str = self.get_name()
            new_name = old_name.split("=")[0] + data
            self.set_name(new_name)
        else:
            raise Exception



class Tree:
    """Pretty empty Tree class to just simulate the add_branch method"""

    def __init__(self):
        self.__root_node = ConnectorNode("")

    def get_root(self):
        return self.__root_node


    def add_branch(self, contents: str, is_list: bool):
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

    def find_node(self, path: str, node: Node, covered_path=None):
        if isinstance(node, VariableNode) or covered_path == []:
            return node
        elif isinstance(node, ConnectorNode):
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
        else:
            raise CrazyError()

    def quick_display(self, node: Node, append: str = ""):
        if isinstance(node, ConnectorNode):
            print(append+node.get_name())
            for i in node.get_connected_nodes():
                self.quick_display(i, append+"  ")
        if isinstance(node, VariableNode):
            print(append+"|--"+node.get_data())
            return
