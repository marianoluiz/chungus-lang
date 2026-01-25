"""Semantic analysis error definitions."""

class SemanticError:
    """Base semantic error."""
    def __init__(self, message: str, line: int, col: int):
        self.message = message
        self.line = line
        self.col = col
    
    def __str__(self):
        return f"Line {self.line}, Col {self.col}: {self.message}"

class UndefinedVariableError(SemanticError):
    """Variable used before declaration."""
    pass

class TypeMismatchError(SemanticError):
    """Operation on incompatible types."""
    pass

class FunctionNotDefinedError(SemanticError):
    """Function call to non-existent function."""
    pass

class ArgumentCountMismatchError(SemanticError):
    """Function called with wrong number of arguments."""
    pass

class VariableAlreadyDefinedError(SemanticError):
    """Variable redeclared in same scope."""
    pass