"""The composer builds the output file if the user applies their changes"""

import re
import os
from dataclasses import dataclass

from nix_tree.errors import NoValidHeadersNode, ErrorComposingFileFromTree
from nix_tree.decomposer import DecomposerTree
from nix_tree.tree import VariableNode, ConnectorNode, Node
from nix_tree.parsing import Types


@dataclass
class ComposerIterator:
    """An iterator that composer uses to build the file"""

    prepend: str = ""  # To store tabs
    previous_prepend: str = ""  # To store prev tabs
    lines: str = ""  # To store current progress
    previous_addition: str = ""  # To store what data was previously added (for comments)


class Composer:
    """The class which contains the functionality to output the edited tree"""

    def __init__(self, tree: DecomposerTree, file_location: str, write_over: bool, comments: bool):
        """Defines the init function to take in the required variables

        Args:
            tree: DecomposerTree - the tree to build the file from
            file_location: str - the location of the file to write to
            write_over: bool - whether to write over the file or append .new to the file name
            comments: bool - whether to include comments from the original file
        """

        self.__tree = tree
        if os.access(file_location, os.W_OK):
            if write_over:
                self.__file_location = file_location
            else:
                self.__file_location = file_location + ".new"
        else:
            print("\033[93m No permission to write to the file/directory containing the original file, writing to current directory instead \033[91m")
            self.__file_location = os.getcwd() + "/" + file_location.split("/")[-1:][0]
        self.__composer_iterator = ComposerIterator()
        self.__write_to_file(comments)

    def __write_to_file(self, comments: bool):
        """Performs the writing by calling the appropriate functions and writing to the file

        Args:
            comments: bool - whether comments should be included from the original file
        """

        self.__separate_and_add_headers()
        if comments:
            self.__work_out_lines_comments(self.__tree.get_root())
        else:
            self.__work_out_lines_no_comments(self.__tree.get_root())
        with open(self.__file_location, "w", encoding="utf-8") as file:
            file.write(self.__composer_iterator.lines + "}\n")

    def __work_out_lines_comments(self, node: Node) -> None:
        """Writes to the file if comments are to be attached

        Args:
            node: Node - the starting node

        Note:
            The only difference between this function and the ordinary work out lines function
            is adding of comments to the end of lines - which requires use of previous_addition
            so that there is no confusing of comments for data 
        """

        comment_for_after = ""
        if node.get_comments():
            for comment in node.get_comments():
                if comment[1]:  # Need to insert above current line (the true false variable in the comment tuple)
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
                        raise ErrorComposingFileFromTree(
                                f"There was an error composing the file from the tree, here is what has been generated already {self.__composer_iterator.lines}"
                        )
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
                        raise ErrorComposingFileFromTree(
                                f"There was an error composing the file from the tree, here is what has been generated already {self.__composer_iterator.lines}"
                        )
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
            if not re.search(r"^''.*''$", node.get_data()):
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
                raise ErrorComposingFileFromTree(
                    f"There was an error composing the file from the tree, the previous character was unexpected, here is what there is currently: {self.__composer_iterator.lines}"
                )
            if len(self.__composer_iterator.prepend) == 2:
                self.__composer_iterator.lines += "\n"
                self.__composer_iterator.previous_addition += "\n"

    def __work_out_lines_no_comments(self, node: Node) -> None:
        """Writes to the file if comments are not to be attached

        Args:
            node: Node - the starting node
        """

        if isinstance(node, ConnectorNode): # Most will be connector nodes
            if len(node.get_connected_nodes()) > 1: # To check if we should split it with curly braecs or not

                # Managing the placing of the start of the group
                if self.__composer_iterator.lines[-1] != ":":
                    if self.__composer_iterator.lines[-1] == ".": # if this is already part of a path like x. already exists
                        self.__composer_iterator.lines += node.get_name() + " = {\n"
                    elif self.__composer_iterator.lines[-1] == "\n": # new line so not part of path - means that the for tabs needs to be added
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + " = {\n"
                    else:
                        raise ErrorComposingFileFromTree(
                                f"There was an error composing the file from the tree, here is what has been generated already {self.__composer_iterator.lines}"
                        )
                else:
                    self.__composer_iterator.lines += "\n\n{\n" # If it is a new file! (only run on first iteration)
                    self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend # need to indent in
                    self.__composer_iterator.prepend += "  "

                # indent managing
                self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend # Updating the prepend (to go down indent later)
                self.__composer_iterator.prepend += "  " # indenting a bit more - we just opened curly braces!

                for singular_node in node.get_connected_nodes():
                    # Recursive calling!
                    self.__work_out_lines_no_comments(singular_node)


                if self.__composer_iterator.previous_prepend != "":
                    self.__composer_iterator.lines += self.__composer_iterator.previous_prepend + "};\n" # Need to shut the group
                else:  # Then it is the end of the file as we have shut the final group (the large {})
                    pass

                # Updating prepends again to go back
                self.__composer_iterator.prepend = self.__composer_iterator.previous_prepend
                self.__composer_iterator.previous_prepend = self.__composer_iterator.previous_prepend[2:]

                # This is to make the base indent level more spaced out
                if len(self.__composer_iterator.prepend) == 2:
                    self.__composer_iterator.lines += "\n"

            elif len(node.get_connected_nodes()) == 1: # If there is only one child

                # Slightly different to above - no curly brace
                if self.__composer_iterator.lines[-1] != ":":
                    if self.__composer_iterator.lines[-1] == ".":
                        self.__composer_iterator.lines += node.get_name() + "."
                    elif self.__composer_iterator.lines[-1] == "\n":
                        self.__composer_iterator.lines += self.__composer_iterator.prepend + node.get_name() + "."
                    else:
                        raise ErrorComposingFileFromTree(
                                f"There was an error composing the file from the tree, here is what has been generated already {self.__composer_iterator.lines}"
                        )
                else:
                    self.__composer_iterator.lines += "\n\n{\n"
                    self.__composer_iterator.previous_prepend = self.__composer_iterator.prepend # need to indent in
                    self.__composer_iterator.prepend += "  "

                # call it for the singular node
                self.__work_out_lines_no_comments(node.get_connected_nodes()[0])
            else:
                pass
        elif isinstance(node, VariableNode):
            # getting "x =" from "y.z.x = gosh" node
            data = node.get_name().split(".")[-1] + " = "

            if node.get_type() == Types.LIST:
                if "'" not in node.get_data(): # If it isnt a list of strings
                    data_as_list = node.get_data().split(" ")
                    data_as_list = data_as_list[1:-1]
                    if len(data_as_list) >= 3: # Splitting the list to multiple lines if longer than 2 elements
                        data += "[\n"
                        for list_item in data_as_list:
                            data += self.__composer_iterator.prepend + "  " + list_item + "\n"
                        data += self.__composer_iterator.prepend + "]"
                    else:
                        data += node.get_data()
                else:
                    data_as_list = node.get_data().split("' '") # note the different splitting required
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
            if not re.search(r"^''.*''$", node.get_data()):
                data = re.sub("'", "\"", data)

            if node.get_type() == Types.LIST and "(" in data:  # needs to be handled with a with clause
                with_clause = data[data.index("(") + 1:data.index(")")]
                data = re.sub(rf"\({with_clause}\)\.", "", data)
                data = data.split("=")[0] + "= with " + with_clause + ";" + data.split("=")[1]

            # handling adding it in
            if self.__composer_iterator.lines[-1] == ".": # end of a connector like x.y now adding z = enable
                self.__composer_iterator.lines += data + ";\n"
            elif self.__composer_iterator.lines[-1] == "\n":
                self.__composer_iterator.lines += self.__composer_iterator.prepend + data + ";\n" # indenting!!!!
            else:
                raise ErrorComposingFileFromTree(
                    f"There was an error composing the file from the tree, the previous character was unexpected, here is what there is currently: {self.__composer_iterator.lines}"
                )

    def __separate_and_add_headers(self) -> None:
        """Separates the headers from the tree and adds them to the file

        Note:
            This is required due to the unique syntax of headers in a Nix file
        """

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
