"""
AST container types used by the recursive-descent parser.

This module defines the minimal, serializable AST node shapes used across the
parser and downstream phases (semantic, codegen, tests). Docstrings on the
dataclasses provide helpful hover/tooltips in editors (VS Code).
"""

from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ASTNode:
    """
    A node in the Abstract Syntax Tree (AST).

    Attributes:
        kind (str): A short name identifying the grammar construct this node
            represents (e.g. 'program', 'function', 'if', 'id', 'int_literal').
        value (Optional[str]): Optional payload used for leaf nodes (identifier
            names, literal text). Non-leaf nodes typically set this to None.
        children (List[ASTNode]): Ordered list of child ASTNode instances that
            represent sub-structure of this node (parameters, body statements, etc).

    Example:
        ASTNode('id', value='x')
        ASTNode('function', value='foo', children=[params_node, body_node])
    """
    kind: str    # grammar construct <program>, <_statement>...
    value: Optional[str] = None     # optional payload (identifier name, literal value, etc.)
    children: List["ASTNode"] = field(default_factory=list) # sub-nodes in the syntax tree
                                                            # default_factory=list: ensures each ASTNode gets its own empty list by default.
                                                            # In python, default argument values are evaluated only once. Well known Mutable default argument
                                                            # or Shared mutable default argument / state across instances
                                                            # So this default_factor list now Call list() every time __init__ runs. this makes sure a.children and b.children, ... are independent and not the same. 
    line: Optional[int] = None
    col: Optional[int] = None


@dataclass
class ParseResult:
    """
    Result object returned by the parser.

    Attributes:
        tree (Optional[ASTNode]): The root AST node produced by a successful
            parse, or None if parsing failed.
        errors (List[str]): List of human-readable parse error messages; empty
            when parsing succeeded.
    """
    tree: Optional[ASTNode]
    errors: List[str]   # structured data (list of error messages)
