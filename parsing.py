"""Stores the parsing class for options checking"""

import json
from enum import Enum
from pathlib import Path


class Types(Enum):
    """This enum defines the possible types for nix variables"""
    BOOL = 0
    INT = 1
    STRING = 2
    UNIQUE = 3
    LIST = 4


class ParsingOptions:
    """This class manages the parsing of the options.json file"""

    def __init__(self, file_path: Path) -> None:
        """The init function takes in the files location and checks if it exists
        before reading it into a string

        Args:
            file_path: Path - a path object containing the file path of the options.json

        Raises:
            FileNotFoundError() - if the file does not exist (or it is a directory)
        """

        if (not file_path.exists()) or (file_path.is_dir()):
            raise FileNotFoundError("The configuration file does not exist")
        self.__options = json.loads(file_path.read_text())

    def check_type(self, option_path: str) -> tuple[Types, str] | None:
        """Searches the options dictionary (generated in init) and returns the type and
        the string found

        Args:
            option_path: str - the path of the option that is being looked for

        Returns:
            tuple(Types, str) - the type found in the string and the full string
        """

        try:
            type_as_string: str = self.__options[option_path]["type"]
        except KeyError:
            return None

        if "boolean" in type_as_string:
            return Types.BOOL, type_as_string
        if "list" in type_as_string:
            return Types.LIST, type_as_string
        if "string" in type_as_string:
            return Types.STRING, type_as_string
        if "integer" in type_as_string:
            return Types.INT, type_as_string
        return None
