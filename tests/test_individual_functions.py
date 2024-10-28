"""Testing individual functions that are not part of classes"""
from pathlib import Path
from random import randint

from textual.widgets import Tree

from nix_tree.section_screens import work_out_full_path
from nix_tree.tree import find_type
from nix_tree.decomposer import Decomposer, DecomposerTree
from nix_tree.parsing import Types

def test_find_type_int():
    """
    Tests the find_type function works for integers
    """
    assert find_type("123") == Types.INT

def test_find_type_bool():
    """
    Tests the find_type function works for booleans 
    """
    assert find_type("true") == Types.BOOL
    assert find_type("false") == Types.BOOL

def test_find_type_list():
    """
    Tests the find_type function works for lists
    """
    assert find_type("[ 'list_obj_1', 'list_obj_2' ]") == Types.LIST

def test_find_type_string():
    """
    Tests the find_type function works for strings
    """
    assert find_type("'string'") == Types.STRING
    assert find_type("''also_string''") == Types.STRING
    assert find_type("'also [] a string but with brackets in for complexity!'") == Types.STRING

def test_work_out_full_path_yasu():
    """
    Tests the work out full path function 15 times on the yasu config
    This test traverses the tree until it reaches a node with no children (storing the path it takes), where it then
    asks the work out full path function to work out the path it took and then it asserts the two paths are the same
    """
    tree = DecomposerTree() # Prepares the normal tree
    Decomposer(Path("./tests/example_configurations/yasu_example_config.nix"), tree) # Fills the normal tree from the example config
    ui_tree = Tree("test") # creates the ui tree
    tree.add_to_ui(tree.get_root(), ui_tree.root) # Fills the UI tree from the normal tree

    for _ in range(0, 15):
        at_bottom_of_tree = False
        path = []
        current_node = ui_tree.root
        while not at_bottom_of_tree:
            if not current_node.is_root: # work out full path func does not include the root node
                path.append(current_node.label.plain)
            if current_node.children:
                valid_indexes = len(current_node.children) - 1
                current_node = current_node.children[randint(0, valid_indexes)]
            else:
                at_bottom_of_tree = True

        assert path == work_out_full_path(current_node, [])


def test_work_out_full_path_pms():
    """
    Tests the work out full path function 15 times on the pms config
    This test traverses the tree until it reaches a node with no children (storing the path it takes), where it then
    asks the work out full path function to work out the path it took and then it asserts the two paths are the same
    """
    tree = DecomposerTree() # Prepares the normal tree
    Decomposer(Path("./tests/example_configurations/pms_example_config.nix"), tree) # Fills the normal tree from the example config
    ui_tree = Tree("test") # creates the ui tree
    tree.add_to_ui(tree.get_root(), ui_tree.root) # Fills the UI tree from the normal tree

    for _ in range(0, 15):
        at_bottom_of_tree = False
        path = []
        current_node = ui_tree.root
        while not at_bottom_of_tree:
            if not current_node.is_root: # work out full path func does not include the root node
                path.append(current_node.label.plain)
            if current_node.children:
                valid_indexes = len(current_node.children) - 1
                current_node = current_node.children[randint(0, valid_indexes)]
            else:
                at_bottom_of_tree = True

        assert path == work_out_full_path(current_node, [])

def test_work_out_full_path_example():
    """
    Tests the work out full path function 15 times on the shortened default config
    This test traverses the tree until it reaches a node with no children (storing the path it takes), where it then
    asks the work out full path function to work out the path it took and then it asserts the two paths are the same
    """
    tree = DecomposerTree() # Prepares the normal tree
    Decomposer(Path("./tests/example_configurations/shortened_default.nix"), tree) # Fills the normal tree from the example config
    ui_tree = Tree("test") # creates the ui tree
    tree.add_to_ui(tree.get_root(), ui_tree.root) # Fills the UI tree from the normal tree

    for _ in range(0, 15):
        at_bottom_of_tree = False
        path = []
        current_node = ui_tree.root
        while not at_bottom_of_tree:
            if not current_node.is_root: # work out full path func does not include the root node
                path.append(current_node.label.plain)
            if current_node.children:
                valid_indexes = len(current_node.children) - 1
                current_node = current_node.children[randint(0, valid_indexes)]
            else:
                at_bottom_of_tree = True

        assert path == work_out_full_path(current_node, [])


