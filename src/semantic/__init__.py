"""
Semantic analysis adapter for CHUNGUS compiler.

This module provides a clean interface to the semantic analyzer,
accepting an AST and source code and producing an annotated AST
with symbol table.
"""

from src.constants.ast import ASTNode
from src.semantic.semantic_analyzer import SemanticAnalyzer, SemanticResult


def analyze_semantic(ast: ASTNode, source: str, debug: bool = False) -> SemanticResult:
    """
    Adapter function for semantic analysis.
    
    Args:
        ast: Root AST node from syntax analysis
        source: Original source code (for error reporting)
        debug: Enable debug output
    
    Returns:
        SemanticResult with annotated AST, errors, and symbol table
    """
    if ast is None:
        return SemanticResult(
            tree=None,
            errors=["Semantic analysis requires a valid AST"],
            symbol_table=None
        )
    
    analyzer = SemanticAnalyzer(ast, source, debug=debug)
    return analyzer.analyze()


__all__ = ['analyze_semantic', 'SemanticAnalyzer', 'SemanticResult']
