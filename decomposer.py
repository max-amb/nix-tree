"""The main python file!"""
from pathlib import Path
import re

from stack import Stack
from tree import *


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

        Returns:
            None

        Note:
            Error handling is managed in the decomposer class, so it does not need to be implemented here
        """
        self.__file_path = file_path
        self.__lines_with_comments: dict[int, str] = {}
        self.__comments_attached_to_line: dict[str, str] = {}

    def extract_comments(self) -> None:
        """Extracts the comments from the file and attaches them to the next line of code

        Args:

        Returns:
            None

        Note:
            This does not handle multiline comments due to it being a prototype - this is to be implemented later
        """
        self.__populate_lines_with_comments()
        self.__attach_comments_to_lines()

    def __populate_lines_with_comments(self) -> None:
        """This method populates the lines_with_comments dictionary with the line number and the comment on that line

        Args:

        Returns:
            None
        """
        with self.__file_path.open(mode='r') as configuration_file:
            for line_num, line in enumerate(configuration_file):
                line = line.strip()
                if "#" in line:
                    self.__lines_with_comments.update({line_num: line})

    def __attach_comments_to_lines(self) -> None:
        """This method attaches comments to the next line

        Args:

        Returns:
            None

        Note:
            Currently this function assumes the next line can be attached to -
            this could be re-attached recursively then, with comments attached to lines done first and then
            comments attached to comments
        """
        with self.__file_path.open(mode='r') as configuration_file:
            lines = configuration_file.readlines()
            for comment_line_num in self.__lines_with_comments:
                self.__comments_attached_to_line.update({
                    self.__lines_with_comments.get(comment_line_num, ""): lines[comment_line_num + 1].strip()
                })

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

    def get_comments_attached_to_line(self) -> dict[str, str]:
        """get the self.__comments_attached_to_line dictionary

        Args:

        Returns:
            comments_attached_to_line: str - the comments attached to line dictionary
        """
        return self.__comments_attached_to_line


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
        comment_handling = CommentHandling(file_path)
        comment_handling.extract_comments()
        self.__reading_the_full_file(comment_handling)
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

    def __reading_the_full_file(self, comment_handling: CommentHandling) -> None:
        """Opens the file and reads it all into one string, possible due to Nix not relying on indentations

        Args:
            comment_handling: CommentHandling - The comment handling object to retrieve a version of the file that
            does not contain comments

        Returns:
            None

        Note:
            This is done to make the file easier to interpret
        """
        self.__full_file: str = ""
        lines = comment_handling.get_file_without_comments()
        for line in lines:
            self.__full_file += line.replace("\n", " ")

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
        self.__tree.add_branch(contents=f"headers=[ {', '.join(headers)}]")

    def __managing_the_rest_of_the_file(self) -> None:
        """Splits the rest of the file into their tokens and adds to the tree

        Returns:
            None

        Note:
            Check the flowchart in the writeup to learn more about this!
        """
        iterator = Iterator()
        rest_of_file: str = self.__cleaning_the_configuration(self.__full_file[self.__full_file.index("}") + 1:])
        groups = self.__forming_groups_dict(rest_of_file)
        rest_of_file_split: list = rest_of_file.split(" ")
        equals_locations: list = self.__finding_equals_signs(rest_of_file_split)
        iterator.previous_prepend = ""

        while iterator.equals_number <= len(equals_locations) - 1:
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
                    self.__tree.add_branch(f"{iterator.prepend}[{', '.join(in_the_brackets)}]")
                    iterator.prepend = iterator.previous_prepend
                case "with":
                    iterator.prepend += self.__checking_group(groups, equals_locations[iterator.equals_number][0])
                    iterator.prepend += rest_of_file_split[equals_locations[iterator.equals_number][1] - 1] + "="
                    in_the_brackets: list = []
                    for phrase_itr in range(equals_locations[iterator.equals_number][1] + 5, len(rest_of_file)):
                        if rest_of_file_split[phrase_itr] == "];":
                            break
                        in_the_brackets.append(rf"({rest_of_file_split[equals_locations[iterator.equals_number][1] + 2]}).{rest_of_file_split[phrase_itr]}")
                    self.__tree.add_branch(rf"{iterator.prepend}[{', '.join(in_the_brackets)}]")
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

    def __finding_equals_signs(self, file: list) -> list:
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
        for phrase_itr in range(len(file)):
            char_location += len(file[phrase_itr])
            if file[phrase_itr] == "=":
                locations.append((char_location, phrase_itr))
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
        file = re.sub("}", " } ", file)
        file = re.sub("{", " { ", file)
        file = re.sub("\"", "'", file)  # For easier handling of strings
        file = re.sub(";", " ; ", file)  # For with clauses
        file = re.sub(r"}\s*;", "}; ", file)
        file = re.sub(r"]\s*;", "]; ", file)
        file = re.sub(r"\s+", " ", file)
        return file

    def __forming_groups_dict(self, file: str) -> dict[str, tuple[int, int]]:
        """Forms the groups dictionary which contains all the groups and their sections

        Args:
            file: str - The configuration file all on one line

        Returns:
            groups: dict[str, tuple[int, int]] - The groups dictionary - sorted due to passing it through the
            function before returning
        """
        groups: dict[str, tuple[int, int]] = {}
        stack = Stack()
        character_iterator = 0
        split_file: list = file.split(" ")
        for phrase_itr in range(len(split_file)):
            character_iterator += len(split_file[phrase_itr])
            if split_file[phrase_itr] == "{":
                stack.push((split_file[phrase_itr - 2], (character_iterator, 0)))
            if split_file[phrase_itr] == "};":
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



