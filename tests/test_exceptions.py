from pathlib import Path
import pytest

from nix_tree.decomposer import Decomposer
from nix_tree.tree import DecomposerTree
from nix_tree.composer import Composer
from nix_tree.errors import NoValidHeadersNode

def test_file_not_found_error():
    """
    Testing that FileNotFoundError is raised when we enter an
    invalid file path into decomposer, e.g. a directory or the file
    doesn't exist
    """

    with pytest.raises(FileNotFoundError) as exception_val:
        Decomposer(Path("/"), DecomposerTree())
    assert str(exception_val.value) == "The configuration file: / does not exist"

def test_no_valid_headers_node_error():
    """
    Testing that if we pass the composer an empty tree, it errors
    out and does not attempt to parse an invalid tree
    """

    decomposer_tree: DecomposerTree = DecomposerTree()
    with pytest.raises(NoValidHeadersNode) as exception_val:
        Composer(decomposer_tree, "", False, False)
    assert str(exception_val.value) == "Could not find any valid headers nodes to start outputting the tree"
