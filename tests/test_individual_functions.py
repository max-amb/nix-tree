from nix_tree.tree import find_type
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
