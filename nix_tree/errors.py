"""Defines some custom errors for use in the program"""


class NodeNotFound(Exception):
    """Raised when the node does not exist in the tree

    Args:
        node_name: str - the name of the node that does not exist in the tree
        message: str - the message to print out with this exception
    """

    def __init__(self, node_name: str, message: str = "Node {NODE} does not exist in the tree"):
        super().__init__(message.format(NODE=node_name))


class CrazyError(Exception):
    """Raised when I have no idea what has happened, should never be raised

    Args:
        message: str - the message to print out with this exception
    """

    def __init__(self, message: str = "How on gods green earth did you get here"):
        super().__init__(message)


class NoValidHeadersNode(Exception):
    """Raised if no valid headers are found by the composer

    Args:
        message: str - the message to print out with this exception
    """
    def __init__(self, message: str = "Could not find any valid headers nodes to start outputting the tree") -> None:
        super().__init__(message)

class ErrorComposingFileFromTree(Exception):
    """Raised if there is an error outputting/composing the tree

    Args:
        message: str - the message to print out with this exception
    """
    def __init__(self, message: str = "an error was encountered composing the file from the tree") -> None:
        super().__init__(message)

class ConfigurationFileNotFound(Exception):
    """Raised if no configuration file is found to edit/read"""
