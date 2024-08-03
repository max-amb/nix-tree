from pathlib import Path
import re
from stack import Stack
from tree import Tree


class Iterator:
    """The iterator object to traverse the file - different to the prototype"""
    equals_number: int = 0
    prepend: str = ""
    previous_prepend: str = ""


class CommentHandling:
    """Class to handle the comments in a Nix file"""

    def __init__(self, file_path: Path):
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

    def __init__(self, file_path: Path):
        """Takes in file path and stores it for the main decomposition function
        
        Args:
            file_path: The file path for the Nix configuration file

        Returns:
            None

        Raises:
            FileNotFoundError: If the file does not exist or is a directory and thus is unreadable
        """

        self.__file_path: Path = file_path
        if (not self.__file_path.exists()) or (self.__file_path.is_dir()):
            raise FileNotFoundError("The configuration file does not exist")
        self.__tree = Tree()
        comment_handling = CommentHandling(file_path)
        comment_handling.extract_comments()
        self.__reading_the_full_file(comment_handling)
        self.__managing_headers()
        self.__managing_the_rest_of_the_file()

    def get_tree(self) -> Tree:
        """Get the current tree maintained by the decomposer"""
        return self.__tree

    def set_tree(self, new_tree: Tree) -> None:
        """Set the tree in the decomposer"""
        self.__tree = new_tree

    def __reading_the_full_file(self, comment_handling: CommentHandling) -> None:
        """Opens the file and reads it all into one string, possible due to Nix not relying on indentations

        Note:
            This is done to make the file easier to interpret

        self.__full_file: str = ""
        with self.__file_path.open(mode='r') as configuration_file:
            lines = configuration_file.readlines()
            for line in lines:
                self.__full_file = self.__full_file + line.replace("\n", " ")
        """
        self.__full_file: str = ""
        lines = comment_handling.get_file_without_comments()
        for line in lines:
            self.__full_file += line.replace("\n", " ")

    def __managing_headers(self) -> None:
        """Adds headers to the tree

        Note:
            Works due to string.index providing the first occurrence - the headers in a Nix file

        """
        string_in_headers: str = self.__full_file[self.__full_file.index("{") + 1:self.__full_file.index("}")]
        for header in string_in_headers.split(","):
            self.__tree.add_branch(contents=f"headers.{header.strip()}", is_var=True)

    def __managing_the_rest_of_the_file(self) -> None:
        """Splits the rest of the file into their tokens and adds to the tree"""
        iterator = Iterator()
        rest_of_file: str = self.__cleaning_the_configuration(self.__full_file[self.__full_file.index("}") + 1:])
        groups = self.__forming_groups_dict(rest_of_file)
        rest_of_file: list = rest_of_file.split(" ")
        equals_locations: list = self.__finding_equals_signs(rest_of_file)
        iterator.previous_prepend = ""
        equals_location = 0
        while equals_location <= len(equals_locations)-1:
            match rest_of_file[equals_locations[equals_location] + 1]:
                case "[":
                    iterator.prepend += rest_of_file[equals_locations[equals_location] - 1] + "."
                    # Should not be an index error unless the Nix file is invalid
                    in_the_brackets: list = []
                    for phrase_itr in range(equals_locations[equals_location]+2, len(rest_of_file)):
                        if rest_of_file[phrase_itr] == "];":
                            break
                        else:
                            in_the_brackets.append(rest_of_file[phrase_itr])
                    for list_item in in_the_brackets:
                        self.__tree.add_branch(iterator.prepend+list_item, True)
                    iterator.prepend = iterator.previous_prepend
                case "with":
                    iterator.prepend += rest_of_file[equals_locations[equals_location] - 1] + "."
                    iterator.prepend += rest_of_file[equals_locations[equals_location] + 2] + "."
                    in_the_brackets: list = []
                    for phrase_itr in range(equals_locations[equals_location]+5, len(rest_of_file)):
                        if rest_of_file[phrase_itr] == "];":
                            break
                        else:
                            in_the_brackets.append(rest_of_file[phrase_itr])
                    for list_item in in_the_brackets:
                        self.__tree.add_branch(iterator.prepend+list_item, True)
                    iterator.prepend = iterator.previous_prepend
            equals_location += 1


    def __finding_equals_signs(self, file: list) -> list:
        locations: list = []
        for phrase_itr in range(len(file)):
            if file[phrase_itr] == "=":
                locations.append(phrase_itr)
        return locations

    def __cleaning_the_configuration(self, file: str) -> str:
        file = re.sub(r"\s+", " ", file)
        file = re.sub("=", " = ", file)
        file = re.sub("}", " } ", file)
        file = re.sub("{", " { ", file)
        file = re.sub(";", " ; ", file) # For with clauses
        file = re.sub(r"}\s*;", "}; ", file)
        file = re.sub(r"]\s*;", "]; ", file)
        file = re.sub(r"\s+", " ", file)
        return file

    def __forming_groups_dict(self, file: str) -> dict[str, tuple[int, int]]:
        """Forms the groups dictionary which contains all the groups within the config file"""
        groups: dict[str, tuple[int, int]] = {}
        stack = Stack()
        character_iterator = 0
        split_file: list = file.split(" ")
        for phrase_itr in range(len(split_file)):
            character_iterator += len(split_file[phrase_itr])
            if split_file[phrase_itr] == "{":
                stack.push((split_file[phrase_itr - 2], (character_iterator, 0)))
            if split_file[phrase_itr] == "}":
                entry = stack.pop()
                starting_point = entry[1][0]
                new_entry_one = (starting_point, character_iterator)
                groups.update({entry[0]: new_entry_one})
        return self.__sort_groups(groups)

    def __sort_groups(self, groups: dict[str, tuple[int, int]]) -> dict[str, tuple[int, int]]:
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


def main():
    """Decomposes the file and adds to the empty add_branch method of the tree class

    Args:

    Returns:
        None

    Raises:
        x
    """
    Decomposer(file_path=Path("/home/max/nea/NEA/configuration.nix"))


if __name__ == "__main__":
    main()
