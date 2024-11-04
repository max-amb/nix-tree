"""Defines some custom errors for use in the program"""


class NodeNotFound(Exception):
    """Raised when the node does not exist in the tree

    Args:
        node_name: str - the name of the node that does not exist in the tree
        message: str - the message to print out with this exception
    """

    def __init__(self, node_name: str, message: str = "Node {NODE} does not exist in the tree"):
        super().__init__(message.format(NODE=node_name))


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
    def __init__(self, message: str = "An error was encountered composing the file from the tree") -> None:
        super().__init__(message)


class ConfigurationFileNotFound(Exception):
    """Raised if no configuration file is found to edit/read"""


class ErrorHandlingComments(Exception):
    """Raised if there was an error with comment management

    Args:
        message: str - the message to print out with this exception
    """
    def __init__(self, line: str, message: str = "There was an error attempting to parse comments on line: {LINE}, \n check all the comments in your config are valid") -> None:
        super().__init__(message.format(LINE=line))
