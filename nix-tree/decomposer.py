"""The module containing the decomposer"""
from pathlib import Path
import re

from stacks import GroupsStack
from tree import DecomposerTree, Node, VariableNode


class Iterator:
    """The iterator object to traverse the file - different to the prototype"""
    equals_number: int = 0
    prepend: str = ""
    previous_prepend: str = ""


class CommentHandling:
    """Class to handle the comments in a Nix file"""

    def __init__(self, file_path: Path) -> None:
        """Takes in the file path of the configuration as a parameter and stores it for use in the methods

        Args:
            file_path: The file path for the Nix configuration file

        Note:
            Error handling is managed in the decomposer class, so it does not need to be implemented here
        """
        self.__file_path = file_path
        self.__lines_with_comments: dict[int, tuple[str, bool]] = {}
        self.__comments: dict[int, list[tuple[str, bool]]] = {}
        self.__populate_lines_with_comments()
        self.__compressing_comments()

    def __populate_lines_with_comments(self) -> None:
        """This method populates the lines_with_comments dictionary with the line number and the comment on that line

        Note:
            If a line is added as true, that means that the line is a lone comment (there is no code on that line)
        """
        with self.__file_path.open(mode='r') as configuration_file:
            for line_num, line in enumerate(configuration_file):
                if re.search(r"^\s*#.*$", line):
                    self.__lines_with_comments.update({line_num: (line, True)})
                elif "#" in line:
                    self.__lines_with_comments.update({line_num: (line, False)})

    def get_file_without_comments(self) -> str:
        """This method deletes the comments from the file

        Args:

        Returns:
            new_file: str - a string which contains the file without any comments

        Note:
            This also acts as a getter for the config without comments
        """
        new_file: str = ""
        with self.__file_path.open(mode="r") as configuration_file:
            for line_num, line in enumerate(configuration_file):
                if line_num in self.__lines_with_comments.keys():
                    split_on_comment: list = line.split("#")
                    new_file += split_on_comment[0]
                else:
                    new_file += line
        return new_file

    def __compressing_comments(self) -> None:
        """Compresses the lines with comments dictionary to get multiline comments into lists"""

        current_addition: list[tuple[str, bool]] = []
        for line_with_comment_itr in range(len(self.__lines_with_comments)):

            if self.__lines_with_comments[list(self.__lines_with_comments.keys())[line_with_comment_itr]][1]:
                current_addition.append((
                    self.__lines_with_comments[list(self.__lines_with_comments.keys())[line_with_comment_itr]][0].strip(),
                    self.__lines_with_comments[list(self.__lines_with_comments.keys())[line_with_comment_itr]][1],
                ))
            else:
                full_line = self.__lines_with_comments[list(self.__lines_with_comments.keys())[line_with_comment_itr]][0]
                comment = full_line.split("#")[1]
                current_addition.append(("#"+comment, False))

            if line_with_comment_itr != len(self.__lines_with_comments) - 1:
                if list(self.__lines_with_comments.keys())[line_with_comment_itr + 1] == \
                        list(self.__lines_with_comments.keys())[line_with_comment_itr] + 1 and \
                        self.__lines_with_comments[list(self.__lines_with_comments.keys())[line_with_comment_itr]][1]:
                    continue
            if not self.__lines_with_comments[list(self.__lines_with_comments.keys())[line_with_comment_itr]][1]:
                self.__comments.update(
                    {list(self.__lines_with_comments.keys())[line_with_comment_itr]: current_addition})
                current_addition = []
            else:
                self.__comments.update(
                    {list(self.__lines_with_comments.keys())[line_with_comment_itr] + 1: current_addition})
                current_addition = []

    def get_comments_for_attaching(self) -> dict[int, list[tuple[str, bool]]]:
        """Returns the cleaned up comments dict

        Returns:
            dict[int, list[tuple[str, bool]]] - the comments dict
        """

        return self.__comments

class Decomposer:
    """Class to handle the decomposition of the Nix file and addition of tokens to the tree"""

    def __init__(self, file_path: Path, tree: DecomposerTree) -> None:
        """Takes in file path and stores it for the main decomposition function
        
        Args:
            file_path: Path - The file path for the Nix configuration file
            tree: DecomposerTree - The tree that decomposer should add to

        Returns:
            None

        Raises:
            FileNotFoundError: If the file does not exist or is a directory and thus is unreadable
        """

        self.__file_path: Path = file_path
        self.__tree: DecomposerTree = tree
        if (not self.__file_path.exists()) or (self.__file_path.is_dir()):
            raise FileNotFoundError("The configuration file does not exist")
        self.__comment_handling = CommentHandling(file_path)
        self.__reading_the_full_file()
        self.__managing_headers()
        self.__managing_the_rest_of_the_file()

    def get_tree(self) -> DecomposerTree:
        """Get the current tree maintained by the decomposer

        Args:

        Returns:
            None
        """
        return self.__tree

    def set_tree(self, new_tree: DecomposerTree) -> None:
        """Set the tree in the decomposer

        Args:

        Returns:
            None
        """
        self.__tree = new_tree

    def __reading_the_full_file(self) -> None:
        """Opens the file and reads it all into one string, possible due to Nix not relying on indentations

        Returns:
            None

        Note:
            This is done to make the file easier to interpret
        """
        self.__full_file: str = ""
        lines = self.__comment_handling.get_file_without_comments()
        for line in lines:
            self.__full_file += line

    def __managing_headers(self) -> None:
        """Adds headers to the tree

        Args:

        Returns:
            None

        Note:
            Works due to string index providing the first occurrence - the headers in a Nix file.
            Also note the space just after the square bracket, this is so it doesn't need to be escaped as if it wasn't
            escaped and there was no space, then there is a rendering error.
        """
        string_in_headers: str = self.__full_file[self.__full_file.index("{") + 1:self.__full_file.index("}")]
        headers: list[str] = []
        for header in string_in_headers.split(","):
            headers.append(header.strip())
        self.__tree.add_branch(contents=f"headers=[ {', '.join(headers)} ]")

    def __prepare_the_file(self, file: str) -> list[str]:
        rest_of_file_split: list = file.split(" ")
        for i, _ in enumerate(rest_of_file_split):
            try:
                if re.search(r"^'\S*\s*[^']$", rest_of_file_split[
                    i]):  # Fixes issue with strings being split on spaces inside the string
                    rest_of_file_split[i] += " " + rest_of_file_split[i + 1]
                    del rest_of_file_split[i + 1]
            except IndexError:
                break  # Index errors are ok because we are deleting from the list
        return rest_of_file_split

    def __managing_the_rest_of_the_file(self) -> None:
        """Splits the rest of the file into their tokens and adds to the tree

        Returns:
            None

        Note:
            Check the flowchart in the writeup to learn more about this!
        """
        comments = self.__comment_handling.get_comments_for_attaching()
        iterator = Iterator()
        rest_of_file: str = self.__cleaning_the_configuration(self.__full_file[self.__full_file.index("}") + 1:])
        groups = self.forming_groups_dict(rest_of_file)
        rest_of_file_split = self.__prepare_the_file(rest_of_file)
        equals_locations: list = self.finding_equals_signs(rest_of_file_split)
        equals_locations = self.__find_equal_locations_lines(equals_locations)
        comments_attached_to_id: dict[str, str] = {}
        iterator.previous_prepend = ""

        while iterator.equals_number <= len(equals_locations) - 1:
            try:
                comment = comments.pop(equals_locations[iterator.equals_number][2])
                comments_attached_to_id.update({
                    self.__checking_group(groups, equals_locations[iterator.equals_number][0]) +
                    rest_of_file_split[equals_locations[iterator.equals_number][1] - 1] :
                    comment
                })
            except KeyError:  # If there isn't a comment attached
                pass
            match rest_of_file_split[equals_locations[iterator.equals_number][1] + 1]:
                case "{":
                    pass  # To stop brackets being added as variables
                case "[":
                    iterator.prepend += self.__checking_group(groups, equals_locations[iterator.equals_number][0])
                    iterator.prepend += rest_of_file_split[equals_locations[iterator.equals_number][1] - 1] + "="
                    # Should not be an index error unless the Nix file is invalid
                    in_the_brackets: list = []
                    for phrase_itr in range(equals_locations[iterator.equals_number][1] + 2, len(rest_of_file)):
                        if rest_of_file_split[phrase_itr] == "];":
                            break
                        in_the_brackets.append(rest_of_file_split[phrase_itr])
                    self.__tree.add_branch(f"{iterator.prepend}[ {' '.join(in_the_brackets)} ]")
                    iterator.prepend = iterator.previous_prepend
                case "with":
                    iterator.prepend += self.__checking_group(groups, equals_locations[iterator.equals_number][0])
                    iterator.prepend += rest_of_file_split[equals_locations[iterator.equals_number][1] - 1] + "="
                    in_the_brackets: list = []
                    for phrase_itr in range(equals_locations[iterator.equals_number][1] + 5, len(rest_of_file)):
                        if rest_of_file_split[phrase_itr] == "];":
                            break
                        in_the_brackets.append(f"({rest_of_file_split[equals_locations[iterator.equals_number][1] + 2]}"
                                               f").{rest_of_file_split[phrase_itr]}")
                    self.__tree.add_branch(f"{iterator.prepend}[ {' '.join(in_the_brackets)} ]")
                    iterator.prepend = iterator.previous_prepend
                case "lib.mkDefault" | "lib.mkForce":
                    iterator.prepend += self.__checking_group(groups, equals_locations[iterator.equals_number][0])
                    iterator.prepend += rest_of_file_split[equals_locations[iterator.equals_number][1] - 1] + "="
                    iterator.prepend += rest_of_file_split[equals_locations[iterator.equals_number][1] + 1] + "."
                    self.__tree.add_branch(iterator.prepend +
                                           rest_of_file_split[equals_locations[iterator.equals_number][1] + 2],
                                           )
                    iterator.prepend = iterator.previous_prepend
                case _:  # Then it is a variable
                    iterator.prepend += self.__checking_group(groups, equals_locations[iterator.equals_number][0])
                    iterator.prepend += rest_of_file_split[equals_locations[iterator.equals_number][1] - 1] + "="
                    self.__tree.add_branch(
                        iterator.prepend + rest_of_file_split[equals_locations[iterator.equals_number][1] + 1])
                    iterator.prepend = iterator.previous_prepend
            iterator.equals_number += 1
        self.__add_comments_to_nodes(self.__tree.get_root(), "", comments_attached_to_id)

    def __checking_group(self, groups: dict[str, tuple[int, int]], location: int) -> str:
        """Checks which group the location in the string is

        Args:
            groups: dict[str, tuple[int, int]] - The groups dictionary
            location: int - the location in the string we want to check

        Returns:
            str - a string containing the groups that need to be added to the start of an option
        """
        to_be_prepended: str = ""
        for group in groups.items():
            if group[1][0] < location < group[1][1]:
                # +2 due to the equals being before the group in theory, hence it wouldn't work
                to_be_prepended += group[0] + "."
        return to_be_prepended

    @staticmethod
    def finding_equals_signs(file: list) -> list:
        """Iterates through the file - split on spaces - to find the equals signs positions

        Args:
            file: list - The list containing the split configuration file

        Returns:
            locations: list - A list containing all the locations of the equals in the file

        Note:
            The tuples used in the locations list allow for the equals locations to be used when the file is split and
            when it is not split
        """
        locations: list = []
        char_location = 0
        for i, phrase in enumerate(file):
            char_location += len(phrase)
            if phrase == "=":
                locations.append((char_location, i))
        return locations

    def __cleaning_the_configuration(self, file: str) -> str:
        """This cleans the configuration with regex substitution to make it possible to tokenize

        Args:
            file: str - the file all on one line

        Returns:
            file: str - the file all on one line now cleaned
        """
        file = re.sub(r"\s+", " ", file)
        file = re.sub("=", " = ", file)
        file = re.sub(r"\s}", " } ", file)
        file = re.sub(r"\s{", " { ", file)
        file = re.sub("\"", "'", file)  # For easier handling of strings
        file = re.sub(";", " ; ", file)  # For with clauses
        file = re.sub(r"}\s*;", "}; ", file)
        file = re.sub(r"]\s*;", "]; ", file)
        file = re.sub(r"(\S*)(];)", r"\1 \2", file)
        file = re.sub(r"\s+", " ", file)
        return file

    def forming_groups_dict(self, file: str) -> dict[str, tuple[int, int]]:
        """Forms the groups dictionary which contains all the groups and their sections

        Args:
            file: str - The configuration file all on one line

        Returns:
            groups: dict[str, tuple[int, int]] - The groups dictionary - sorted due to passing it through the
            function before returning
        """
        groups: dict[str, tuple[int, int]] = {}
        stack = GroupsStack()
        character_iterator = 0
        split_file: list = file.split(" ")
        for i, phrase in enumerate(split_file):
            character_iterator += len(phrase)
            if phrase == "{":
                stack.push((split_file[i - 2], (character_iterator, 0)))
            if phrase == "};":
                entry = stack.pop()
                starting_point = entry[1][0]
                new_entry_one = (starting_point, character_iterator)
                groups.update({entry[0]: new_entry_one})
        return self.__sort_groups(groups)

    def __sort_groups(self, groups: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int]]:
        """Sorts the groups based on size in descending order

        Args:
            groups: dict[str, tuple[int, int]] - The groups passed in - unordered

        Returns:
            new_groups: dict[str, tuple[int, int]] - The groups now sorted with the largest width first
        """
        new_groups: dict[str, tuple[int, int]] = {}
        while len(groups) > 0:
            maximum_size: int = 0  # To get infinity in python
            largest_group: tuple[str, tuple[int, int]] = ("", (0, 0))
            for group in groups.items():
                if group[1][1] - group[1][0] > maximum_size:
                    largest_group = (group[0], (group[1][0], group[1][1]))
                    maximum_size = group[1][1] - group[1][0]
            groups.pop(largest_group[0])
            new_groups.update({largest_group[0]: (largest_group[1][0], largest_group[1][1])})
        return new_groups

    def __find_equal_locations_lines(self, equals_locations: list) -> list:
        lines: list[str] = self.__file_path.open(mode='r').readlines()

        # Cleaning
        for i, line in enumerate(lines):
            lines[i] = lines[i].strip()
            if "#" in line:
                lines[i] = lines[i].split("#")[0].strip()

        equals_num = 0
        for i, line in enumerate(lines):
            number_of_equals = line.count("=")
            for _ in range(number_of_equals):
                equals_locations[equals_num] = (equals_locations[equals_num][0], equals_locations[equals_num][1], i)
                equals_num += 1
        return equals_locations

    def __add_comments_to_nodes(self, node: Node, prepend: str, comments: dict[str, str]):
        prepend += "."+node.get_name().split("=")[0]
        try:
            if isinstance(node, VariableNode):
                comment = comments.pop(node.get_name())
                node.set_comments(comment)
            else:
                comment = comments.pop(prepend[2:])
                node.set_comments(comment)
        except KeyError:
            pass
        for child in node.get_connected_nodes():
            self.__add_comments_to_nodes(child, prepend, comments)
