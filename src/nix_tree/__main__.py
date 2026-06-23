"""Handles user command line interaction"""

import argparse
from pathlib import Path

from nix_tree.ui import start_ui
from nix_tree.errors import ConfigurationFileNotFound


def main():
    """Parses the arguments to the tool and passes it on to the rest of the code"""

    parser = argparse.ArgumentParser(prog="nix-tree",
                                     description="A tool for viewing and editing your nix configuration as a tree")
    parser.add_argument("file_location", type=str,
                        help="The location of your nix configuration file")
    parser.add_argument("-w", "--writeover", default=False, action="store_true",
                        help="Write over the file that you are editing")
    parser.add_argument("-c", "--comments", default=False, action="store_true",
                        help="Whether you would like comments to be copied over from the original file")
    args = parser.parse_args()
    configuration_file = Path(args.file_location)
    if configuration_file.is_file():
        start_ui(args.file_location, args.writeover, args.comments)
    else:
        raise ConfigurationFileNotFound


if __name__ == "__main__":
    main()
