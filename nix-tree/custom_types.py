"""Defines two custom types for use in the ui mostly"""

from textual.widgets import Tree, _tree
"""Need to import Tree to import _tree"""

type UIVariableNode = _tree.TreeNode[dict]
type UIConnectorNode = _tree.TreeNode  # Connector nodes for unknown cases
