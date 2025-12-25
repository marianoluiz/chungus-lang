from dataclasses import dataclass

@dataclass
class Token:
    lexeme: str
    type: str
    line: int
    col: int