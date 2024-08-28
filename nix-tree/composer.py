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
    previous_addition: str = ""

class Composer:
    def __init__(self, decomposer: Decomposer, file_location: str, write_over: bool, comments: bool):
        self.__decomposer: Decomposer = decomposer
        self.__tree: DecomposerTree = decomposer.get_tree()
        if write_over:
            self.__file_location = file_location
        else:
            self.__file_location = file_location + ".new"
        self.__composer_iterator = ComposerIterator()
        self.write_to_file(comments)

    def write_to_file(self, comments: bool):
        self.__separate_and_add_headers()
        if comments:
            self.__work_out_lines_comments(self.__tree.get_root())
        else:
            self.__work_out_lines_no_comments(self.__tree.get_root())
        with open(self.__file_location, "w", encoding="utf-8") as file:
            file.write(self.__composer_iterator.lines + "}\n")

    def __work_out_lines_comments(self, node: Node) -> None:
        comment_for_after = ""
        if node.get_comments():
            for comment in node.get_comments():
                if comment[1]: # Need to insert above current line
                    before_comment = self.__composer_iterator.lines.split("\n")[:-1]
                    post_comment = self.__composer_iterator.lines.split("\n")[-1]
                    before_comment_str = '\n'.join(before_comment) + "\n" + self.__composer_iterator.prepend + comment[0]
                    self.__composer_iterator.lines = before_comment_str.strip() + "\n" + post_comment
                else:
                    comment_for_after = comment[0]
        if isinstance(node, ConnectorNode):
            if len(node.get_connected_nodes()) > 1:
                if self.__composer_iterator.previous_addition[-1] != ":":
                    if self.__composer_iterator.previous_addition[-1] == ".":
                        self.__composer_iterator.lines += node.get_name() + " = {\n" + comment_for_after
                        self.__composer_iterator.previous_addition = node.get_name() + " = {\n"
                    elif self.__composer_iterator.previous_addition[-1] == "\n":
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + " = {\n" + comment_for_after
                        self.__composer_iterator.previous_addition = self.__composer_iterator.prepend + node.get_name() + " = {\n"
                    else:
                        raise CrazyError(self.__composer_iterator.lines)
                else:
                    self.__composer_iterator.lines += "\n\n{\n"
                    self.__composer_iterator.previous_addition = "\n\n{\n"
                self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend
                self.__composer_iterator.prepend += "  "
                for singular_node in node.get_connected_nodes():
                    self.__work_out_lines_comments(singular_node)

                if self.__composer_iterator.previous_prepend != "":
                    self.__composer_iterator.lines += self.__composer_iterator.previous_prepend + "};\n"
                    self.__composer_iterator.previous_addition = self.__composer_iterator.previous_addition + "};\n"
                else:  # Then it is the end of the file
                    pass
                self.__composer_iterator.prepend = self.__composer_iterator.previous_prepend
                self.__composer_iterator.previous_prepend = self.__composer_iterator.previous_prepend[2:]
                if len(self.__composer_iterator.prepend) == 2:
                    self.__composer_iterator.lines += "\n"
                    self.__composer_iterator.previous_addition += "\n"
            elif len(node.get_connected_nodes()) == 1:
                if self.__composer_iterator.previous_addition[-1] != ":":
                    if self.__composer_iterator.previous_addition[-1] == ".":
                        self.__composer_iterator.lines += node.get_name() + "."
                        self.__composer_iterator.previous_addition = node.get_name() + "."
                    elif self.__composer_iterator.lines[-1] == "\n":
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + "."
                        self.__composer_iterator.previous_addition = self.__composer_iterator.prepend + node.get_name() + "."
                    else:
                        raise CrazyError(self.__composer_iterator.lines)
                else:
                    self.__composer_iterator.lines += "\n\n{\n"
                    self.__composer_iterator.previous_addition += "\n\n{\n"
                    self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend
                    self.__composer_iterator.prepend += "  "
                self.__work_out_lines_comments(node.get_connected_nodes()[0])
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

            if self.__composer_iterator.previous_addition[-1] == ".":
                if comment_for_after != "":
                    self.__composer_iterator.lines += data + "; " + comment_for_after
                else:
                    self.__composer_iterator.lines += data + ";\n"
                self.__composer_iterator.previous_addition = data + ";\n"
            elif self.__composer_iterator.previous_addition[-1] == "\n":
                if comment_for_after != "":
                    self.__composer_iterator.lines += self.__composer_iterator.prepend + data + "; " + comment_for_after
                else:
                    self.__composer_iterator.lines += self.__composer_iterator.prepend + data + ";\n"
                self.__composer_iterator.previous_addition = self.__composer_iterator.prepend + data + ";\n"
            else:
                raise CrazyError
            if len(self.__composer_iterator.prepend) == 2:
                self.__composer_iterator.lines += "\n"
                self.__composer_iterator.previous_addition += "\n"

    def __work_out_lines_no_comments(self, node: Node) -> None:
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
                    self.__work_out_lines_no_comments(singular_node)
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
                self.__work_out_lines_no_comments(node.get_connected_nodes()[0])
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
                self.__composer_iterator.previous_addition = "}:"
            self.__tree.get_root().remove_child_variable_node(headers_node.get_name() + "=" + headers_node.get_data())
        else:
            raise NoValidHeadersNode
