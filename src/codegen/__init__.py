"""
Code generation adapter for CHUNGUS compiler.

This module provides a clean interface to the code generator,
accepting a type-annotated AST from semantic analysis and
producing executable output.
"""

from typing import Optional
from dataclasses import dataclass
from src.constants.ast import ASTNode
from src.semantic.semantic_analyzer import SymbolTable


@dataclass
class CodeGenResult:
    """
    Result object returned by the code generator.
    
    Attributes:
        code (Optional[str]): Generated code output, or None if generation failed
        errors (List[str]): List of code generation error messages
        success (bool): Whether code generation succeeded
    """
    code: Optional[str]
    errors: list[str]
    success: bool


def analyze_codegen(ast: ASTNode, source: str = "", symbol_table: Optional[SymbolTable] = None, debug: bool = False) -> CodeGenResult:
    """
    Adapter function for code generation.
    
    Args:
        ast: Type-annotated AST from semantic analysis
        source: Original source code (for error reporting)
        symbol_table: Symbol table from semantic analysis (optional)
        debug: Enable debug output
    
    Returns:
        CodeGenResult with generated code or errors
    """
    from src.codegen.code_generator import CodeGenerator
    
    if ast is None:
        return CodeGenResult(
            code=None,
            errors=["Code generation requires a valid AST"],
            success=False
        )
    
    generator = CodeGenerator(ast, source, symbol_table=symbol_table, debug=debug)
    return generator.generate()
