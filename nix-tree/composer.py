"""Composer"""

import re

from errors import NoValidHeadersNode, CrazyError
from decomposer import Decomposer, DecomposerTree
from tree import VariableNode, ConnectorNode, Node
from parsing import Types

class ComposerIterator:
    """An iterator that composer uses to build the file"""

    prepend: str = ""
    previous_prepend: str = ""
    lines: str = ""

class ComposerIteratorEdit:
    equals_number = 0
    file = ""
    file_split = []
    groups_dict = {}
    equals_locations = []

class Composer:
    def __init__(self, decomposer: Decomposer, file_location: str, write_over: bool, operations: list[str]):
        self.__decomposer: Decomposer = decomposer
        self.__tree: DecomposerTree = decomposer.get_tree()
        self.__operations: list[str] = operations
        self.__comments: dict[str, str] = decomposer.get_comments_attached_to_line()
        if write_over:
            self.__file_location = file_location
        else:
            self.__file_location = file_location + ".new"
        self.__composer_iterator = ComposerIterator()
        self.write_to_file()

    def write_to_file(self):
        self.__separate_and_add_headers()
        self.__work_out_lines(self.__tree.get_root())
        with open(self.__file_location, "w", encoding="utf-8") as file:
            file.write(self.__composer_iterator.lines + "}\n")

    def __work_out_lines(self, node: Node) -> None:
        if isinstance(node, ConnectorNode):
            if len(node.get_connected_nodes()) > 1:
                if self.__composer_iterator.lines[-1] != ":":
                    if self.__composer_iterator.lines[-1] == ".":
                        self.__composer_iterator.lines += node.get_name() + " = {\n"
                    elif self.__composer_iterator.lines[-1] == "\n":
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + " = {\n"
                    else:
                        raise CrazyError(self.__composer_iterator.lines)
                else:
                    self.__composer_iterator.lines += "\n\n{\n"
                self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend
                self.__composer_iterator.prepend += "  "
                for singular_node in node.get_connected_nodes():
                    self.__work_out_lines(singular_node)
                if self.__composer_iterator.previous_prepend != "":
                    self.__composer_iterator.lines += self.__composer_iterator.previous_prepend + "};\n"
                else:  # Then it is the end of the file
                    pass
                self.__composer_iterator.prepend = self.__composer_iterator.previous_prepend
                self.__composer_iterator.previous_prepend = self.__composer_iterator.previous_prepend[2:]
                if len(self.__composer_iterator.prepend) == 2:
                    self.__composer_iterator.lines += "\n"
            elif len(node.get_connected_nodes()) == 1:
                if self.__composer_iterator.lines[-1] != ":":
                    if self.__composer_iterator.lines[-1] == ".":
                        self.__composer_iterator.lines += node.get_name() + "."
                    elif self.__composer_iterator.lines[-1] == "\n":
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + "."
                    else:
                        raise CrazyError(self.__composer_iterator.lines)
                else:
                    self.__composer_iterator.lines += "\n\n{\n"
                    self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend
                    self.__composer_iterator.prepend += "  "
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

    def __work_on_existing_file(self) -> None:
        self.__iterator = ComposerIteratorEdit()
        self.__iterator.file = self.__decomposer.get_file()
        self.__iterator.groups_dict = self.__decomposer.forming_groups_dict(self.__iterator.file)
        self.__iterator.file_split = self.__decomposer.prepare_the_file(self.__iterator.file)
        self.__iterator.equals_locations = self.__decomposer.finding_equals_signs(self.__iterator.file_split)
        for operation in self.__operations:
            if operation.split(" ")[0] == "Change":
                self.__change_operation(operation)
            else:
                raise Exception(operation)

    def __change_operation(self, operation: str):
        change_command: str = operation[7:]  # Can't use space splits as it changes the lists spaces
        pre: list = change_command.split("->")[0].strip().split("=")
        post: list = change_command.split("->")[1].strip().split("=")
        while self.__iterator.equals_number <= len(self.__iterator.equals_locations) - 1:
            if self.__iterator.file_split[self.__iterator.equals_locations[self.__iterator.equals_number][1] + 1].strip() == "{":
                self.__iterator.equals_number += 1
            else: 
                group_in = self.__decomposer.checking_group(self.__iterator.groups_dict, self.__iterator.equals_locations[self.__iterator.equals_number][0])
                raise Exception(self.__iterator.groups_dict)
                before_the_equals = self.__iterator.file_split[self.__iterator.equals_locations[self.__iterator.equals_number][1] -1 ]
                full_path = group_in + before_the_equals
                raise Exception(full_path)
                if full_path == pre[0]:
                    # re.match(r"(.*)ports\s*=[^;]*(.*)", self.__iterator.file)
                    raise Exception(self.__iterator.file)
                else:
                    self.__iterator.equals_number += 1
