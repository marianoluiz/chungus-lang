from dataclasses import dataclass, field
from src.lexer.dfa_lexer import Lexer 
from typing import List, Optional, Tuple
from src.constants.token import Token

@dataclass
class ASTNode:
    kind: str    # grammar construct <program>, <_statement>...
    value: Optional[str] = None     # optional payload (identifier name, literal value, etc.)
    children: List["ASTNode"] = field(default_factory=list) # sub-nodes in the syntax tree

@dataclass
class ParseResult:
    tree: Optional[ASTNode]
    errors: List[str]   # structured data (list of error messages)


class ParseError(Exception):
    """Exception raised for parse errors."""
    def __init__(self, message):
        super().__init__(message)

class UnexpectedError:
    """ Display carret block error """
    def __init__(self, line: str, position: tuple[int, int]):
        self._line = line.replace('\n', '')
        self._position = position  # (1-based line, 1-based col)

    def __str__(self):
        line_no = max(1, int(self._position[0]))
        col_no = max(1, int(self._position[1]))
        return (
            f"\n{line_no:<5}|{self._line}\n"
            f"     |{' '*(col_no-1)}^\n"
        )


# Terminal token type names used by grammar
ID_T = 'id'
INT_LIT_T = 'int_literal'
FLOAT_LIT_T = 'float_literal'
STR_LIT_T = 'str_literal'

KEYWORDS = {
    'and','or','true','false','read','show','if','elif','else','while','for','in','range',
    'fn','ret','try','fail','always','todo','array_add','array_remove','int','float','close'
}
OPERATORS = {
    '++','--','//','**','==','!=','>','<','>=','<=','+','-','*','/','%','(',')','[',']',',','=','!'
}

SKIP_TOKENS = {"whitespace", "newline"}

LITERAL_TYPES = {INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, 'true', 'false'}

class RDParser:
    """
    Recursive-Descent Parser (RDParser).

    Parses a stream of Tokens (produced by the Lexer) into an Abstract Syntax Tree (AST).

    Attributes:
        tokens (List[Token]): List of tokens to parse.
        _source (str): Original source code string.
        _lines (List[str]): Source code split into lines for error reporting.
        _i (int): Current token index.
        errors (List[str]): List of parse error messages encountered.
        _debug (bool): Debug mode flag. Prints debug messages if True.

    Grammar Support:
        - Functions: 'fn' ... 'close'
        - Statements: 'show', 'ret', etc.
        - Expressions: logical, arithmetic, relational, function calls, array indexing
        - Literals: int, float, string, boolean
        - Identifiers

    See `docs/ast_structure.md` for full AST node hierarchy.
    """
    def __init__(self, tokens: List[dict], source: str, debug: bool = False):
        self.tokens: List[Token] = tokens   #  [ Token(lexeme, type, line, col), ... ]
        self._source = source
        self._lines = source.splitlines(keepends=False)
        self._i = 0                # current token index
        self.errors: List[str] = []
        self._debug = debug        # Debug switch

    def _dbg(self, msg: str):
        """ Debugging print message """
        if self._debug:
            print(msg)
    
    # --------------------- Helpers ---------------------
    def _skip_trivia(self):
        """
        Skip non-essential tokens such as whitespace and newline.
        Advances the token index to the next significant token.
        """
        while self._i < len(self.tokens) and \
            self.tokens[self._i].type in SKIP_TOKENS:
            self._i += 1
    
    def _curr(self) -> dict:
        """
        Get the current token after skipping trivia.

        Returns:
            Token: The current Token object, or a synthetic EOF token if at end.
        """
        self._skip_trivia()
        if self._i >= len(self.tokens):
            # Place EOF at the end of the last source line so the caret prints after the line text.
            if self._lines:
                line_no = len(self._lines)              # Length of whole program from the lines list
                col_no = len(self._lines[-1]) + 1       # In the last line, the length of it
            else:
                line_no = 1
                col_no = 1

            return Token(type="EOF", lexeme="", line=line_no, col=col_no)
        
        return self.tokens[self._i]

    def _match(self, *types: str) -> bool:
        """
        Check if the current token's type matches any of the given types.

        Args:
            *types: Variable length token type arguments to match.

        Returns:
            bool: True if the current token type matches any of the types, False otherwise.
        """
        return self._curr().type in types
    
    def _advance(self) -> dict:
        """
        Consume the current token and move the pointer forward.

        Returns:
            Token: The token that was consumed.
        """
        self._skip_trivia()
        tok = self._curr()
        if tok.type != 'EOF':
            self._i += 1
        return tok
    
    def _error(self, expected: List[str], context: str):
        """
        Raise a ParseError with a detailed caret-style message.

        Args:
            expected (List[str]): List of expected token types.
            context (str): Description of the parsing context (e.g., 'function_name').

        Raises:
            ParseError: Always raises with formatted error message.
        """
        tok = self._curr()

        # If tok.line is a valid line number, get that line from self._lines; otherwise use an empty string
        line_text = self._lines[tok.line - 1] if 1 <= tok.line <= len(self._lines) else ""
        
        err_block = str(UnexpectedError(line_text, (tok.line, tok.col)))
        expected_list = ", ".join(sorted(expected))
        msg = (
            f"{err_block}"
            f"Unexpected token in {context} at line {tok.line} col {tok.col}: "
            f"{tok.type or tok.lexeme}\n"
            f"Expected any: {expected_list}"
        )
        
        # Stop parsing immediately
        raise ParseError(msg)

    def parse(self) -> ParseResult:
        """
        Parse the token stream into an AST.

        Returns:
            ParseResult: Contains the root ASTNode and list of errors encountered.
        """
        try:
            tree = self._program()
            return ParseResult(tree, self.errors)
        except ParseError as e:
            # Store error in list
            self.errors.append(str(e))
            return ParseResult(None, self.errors)
        
    
    # --------------------- Grammar ---------------------
    

    # --- Program ---
    def _program(self) -> ASTNode:
        """
        Parse the top-level program structure.

        Returns:
            ASTNode: Root ASTNode representing the program.
        """
        funcs = self._function_statements()
        general_stmts = [self._general_statement()]

        while not self._match('EOF'):
            general_stmts.append(self._general_statement())

        children = funcs + general_stmts
        return ASTNode('program', children=children)

    def _function_statements(self) -> List[ASTNode]:
        """
        Parse a sequence of function declarations.

        Returns:
            List[ASTNode]: List of function AST nodes.
        """
        nodes = []
        while self._match('fn'):
            nodes.append(self._function_statement())
        return nodes
        
    # --- Function ---
    def _function_statement(self) -> ASTNode:
        """
        Parse a single function declaration.

        Returns:
            ASTNode: AST node representing the function with children nodes for parameters, locals, and return.
        """
        self._advance()  # consume 'fn'
    
        # check if next is id or else error
        if self._match(ID_T):
            fn_name = self._advance().lexeme
        else:
            self._error([ID_T], 'function_name')

        # check if next is ( or else error
        if self._match('('):
            self._advance()
            params = self._arg_list_opt()
            
            # check if next is ) or else error
            if self._match(')'):
                self._advance()
            else:
                self._error([')'], 'function_declaration')

        else:
            self._error(['('], 'function_declaration')

        # check inside the function block
        fn_nodes = []

        # require 1 local statement
        fn_nodes.append(self._general_statement())

        while not self._match('ret', 'close'):
            fn_nodes.append(self._general_statement())

        ret_node = self._return_opt()

        if self._match('close'):
            self._advance()
        else:
            self._error(['close'], 'function_declaration')

        # We will add 1. params, then 2. local_nodes, then 3. ret_nodes
        children = []

        if params:
            children.append(ASTNode('params', children=params))
        
        children.extend(fn_nodes)

        if ret_node:
            children.append(ret_node)

        return ASTNode('function', value=fn_name, children=children)


    def _arg_list_opt(self) -> List[ASTNode]:
        """
        Parse an optional comma-separated argument list.

        Returns:
            List[ASTNode]: List of expression AST nodes representing arguments.
        """
        args: List[ASTNode] = []

        # tokens that can legally follow a completed expression inside parentheses
        FOLLOW_AFTER_ARG = {
            '!=', '%', ')', '*', '**', '+', ',', '-', '/', '//', '<', '<=', '==', '>', '>=', 'and', 'or'
        }

        FOLLOW_ID_POSTFIX = {'(', '['}  # only valid after id in expressions
        FOLLOW_NESTED_INDEX = {'['}     # only valid after index postfix in expressions

        if not self._match(')'):
            # parse expression if not empty 
            node = self._expr()
            args.append(node)

            # If after parsing an expression we don't see a comma, a closing paren,
            # or any operator that can continue the expression, produce a clearer error.
            allowed = FOLLOW_AFTER_ARG

            if node.kind in ('id'):
                allowed = allowed | FOLLOW_ID_POSTFIX # adds all elements from POSTFIX_TOKS into allowed.

            if node.kind in ('index'):
                allowed = allowed | FOLLOW_NESTED_INDEX # adds all elements from FOLLOW_NESTED_INDEX into allowed.

            if not self._match(*allowed):
                self._error(sorted(list(allowed)), 'function_declaration')

            # additional comma-separated expressions
            while self._match(','):
                self._advance()
                node = self._expr()
                args.append(node)

                # If we don't see a comma, a closing paren,
                # or any operator that can continue the expression, produce a clearer error.
                allowed = FOLLOW_AFTER_ARG

                if node.kind in ('id'):
                    allowed = allowed | FOLLOW_ID_POSTFIX # adds all elements from POSTFIX_TOKS into allowed.

                if node.kind in ('index'):
                    allowed = allowed | FOLLOW_NESTED_INDEX # adds all elements from POSTFIX_TOKS into allowed.

                if not self._match(*allowed):
                    self._error(sorted(list(allowed)), 'function_declaration')

        return args
    

    # --- Expr ---
    def _expr(self) -> ASTNode:
        """
        Parse an expression (logical OR).

        Returns:
            ASTNode: Expression AST node.
        """
        return self._logical_or_expr()
    
    def _logical_or_expr(self) -> ASTNode:
        """
        Parse logical OR expressions.

        Returns:
            ASTNode: AST node representing logical OR operations.
        """
        left  = self._logical_and_expr()

        while self._match('or'):
            op = self._advance().lexeme
            right = self._logical_and_expr()
            left = ASTNode(op, children=[left, right])
        return left
    
    def _logical_and_expr(self) -> ASTNode:
        """
        Parse logical AND expressions.

        Returns:
            ASTNode: AST node representing logical AND operations.
        """

        # Advance handle errors
        expected = [ '!', '(', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true' ]

        if not self._match(*expected):
            return self._error(expected, 'logical_or_expr')

        left = self._logical_not_expr()

        while self._match('and'):
            op = self._advance().lexeme
            right = self._logical_not_expr()
            left = ASTNode(op, children=[left, right])
        return left

    def _logical_not_expr(self) -> ASTNode:
        """
        Parse logical NOT expressions.

        Returns:
            ASTNode: AST node representing logical NOT operation or the next expression.
        """

        # Advance handle errors
        expected = [ '!', '(', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true' ]

        if not self._match(*expected):
            return self._error(expected, 'logical_and_expr')

        if self._match('!'):
            self._advance()

            right = self._eq_expr()
            return ASTNode('!', children=[right])
        
        # go to production where theres no !
        return self._eq_expr() 

    def _eq_expr(self) -> ASTNode:
        """
        Parse equality expressions (==, !=).

        Returns:
            ASTNode: AST node representing equality operations.
        """

        left = self._comp_operand()

        while self._match('==', '!='):
            op = self._advance().lexeme
            right = self._comp_operand()
            left = ASTNode(op, children=[left, right])
        
        return left
    
    def _comp_operand(self) -> ASTNode:
        """
        Parse a comparison operand: literal, boolean, or relational expression.

        Returns:
            ASTNode: AST node representing the operand.
        """

        # Advance handle errors
        expected = [ '(', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true' ]

        if not self._match(*expected):
            return self._error(expected, 'comp_operand')

        # can be rel_expr, str_literal, true, false
        if self._match(STR_LIT_T):
            return ASTNode('str_literal', value=self._advance().lexeme)
        
        if self._match('true', 'false'):
            return ASTNode('bool_literal', value=self._advance().lexeme)
        
        return self._rel_expr()


    def _rel_expr(self) -> ASTNode:
        """
        Parse relational expressions (>, >=, <, <=).

        Returns:
            ASTNode: AST node representing relational operations.
        """
        left = self._arith_expr()

        while self._match('>', '>=', '<', '<='):
            op = self._advance().lexeme
            right = self._arith_expr()
            left = ASTNode(op, children=[left, right])
        
        return left

    def _arith_expr(self) -> ASTNode:
        """
        Parse arithmetic expressions (+, -).

        Returns:
            ASTNode: AST node representing addition/subtraction operations.
        """
        left = self._term()

        while self._match('+', '-'):
            op = self._advance().lexeme
            right = self._term()
            left = ASTNode(op, children=[left, right])
        
        return left

    def _term(self) -> ASTNode:
        """
        Parse multiplicative expressions (*, /, //, %).

        Returns:
            ASTNode: AST node representing multiplication/division/modulo operations.
        """
        left = self._factor()

        while self._match('*', '/', '//', '%'):
            op = self._advance().lexeme
            right = self._factor()
            left = ASTNode(op, children=[left, right])
        
        return left
    
    def _factor(self) -> ASTNode:
        """
        Parse power expressions (**).

        Returns:
            ASTNode: AST node representing power operations.
        """
        left = self._power()

        while self._match('**'):
            op = self._advance().lexeme
            right = self._power()
            left = ASTNode(op, children=[left, right])
        
        return left
    
    def _power(self) -> ASTNode:
        """
        Parse primary expressions: literals, identifiers, function calls, grouping.

        Returns:
            ASTNode: AST node representing the primary expression.
        """
        if self._match(INT_LIT_T, FLOAT_LIT_T):
            tok = self._advance()
            kind = INT_LIT_T if tok.type == INT_LIT_T else FLOAT_LIT_T
            return ASTNode(kind, value=tok.lexeme)
        
        if self._match(STR_LIT_T):
            tok = self._advance()
            return ASTNode('str_literal', value=tok.lexeme)
        
        if self._match(ID_T):
            tok = self._advance()
            node = ASTNode('id', value=tok.lexeme)

            # handle function call or indexing
            if self._match('(', '['):
                node = self._postfix_tail(node)

            return node

        if self._match('('):
            self._advance()
            node = self._expr()

            if self._match(')'):
                self._advance()
                return node
            else:
                self._error([')'], 'expression')
                return node

        self._error([INT_LIT_T, FLOAT_LIT_T, ID_T, '('], 'power')


    def _postfix_tail(self, node: ASTNode) -> ASTNode:
        """
        Parse postfix operations: function calls and array indexing.

        Args:
            node (ASTNode): Base AST node (identifier).

        Returns:
            ASTNode: AST node after applying postfix operations.
        """
        if self._match('('):
            self._advance()

            args = self._arg_list_opt()

            if self._match(')'):
                self._advance()
            else:
                self._error([')'], 'function_call')
            return ASTNode('function_call', value=node.value, children=args)
        
        # flattened indexes
        indices = []

        while self._match('['):
            # array indexing / loop
            self._advance()

            idx = self._expr()
            indices.append(idx)

            if self._match(']'):
                self._advance()
            else:
                self._error([']'], 'index')
        
        # if it is array reference
        if indices:
            return ASTNode('index', children=[node] + indices)
        
        # if it is function call
        return node

    def _return_opt(self) -> Optional[ASTNode]:
        """
        Parse an optional return statement.

        Returns:
            ASTNode | None: AST node for return statement if present.
        """

        FOLLOW_AFTER_RET = {
            '!=', '%', '*', '**', '+', '-', '/', '//', '<', '<=', '==', '>', '>=', 'and', 'close', 'or'
        }

        if self._match('ret'):
            self._advance()

            node =  ASTNode('return_statement', children=[self._expr()])

            if not self._match(*FOLLOW_AFTER_RET):
                self._error(sorted(list(FOLLOW_AFTER_RET)), 'return')

            return node
        
        return None
    
    def _general_statement(self) -> ASTNode:
        """
        Parse a general statement (e.g., output, control statements).

        Returns:
            ASTNode: AST node representing the statement.
        """

        # identifier-starting statement (assignment, call, unary, indexed assignment)
        if self._match(ID_T):
            id_name = self._advance().lexeme
            node = self._id_statement_tail(id_name)
            return ASTNode('general_statement', children=[node])

        # output
        elif self._match('show'):
            node = self._output_statement()
            return ASTNode('general_statement', children=[node])

        # conditional (if / elif / else ... close)
        elif self._match('if'):
            node = self._conditional_statement()
            return ASTNode('general_statement', children=[node])

        # looping (for / while)
        elif self._match('for', 'while'):
            node = self._looping_statement()
            return ASTNode('general_statement', children=[node])

        # error handling (try / fail / always ... close)
        elif self._match('try'):
            node = self._error_handling_statement()
            return ASTNode('general_statement', children=[node])

        # todo
        elif self._match('todo'):
            self._advance()
            return ASTNode('general_statement', children=[ASTNode('todo')])

        # array manipulation helpers
        elif self._match('array_add', 'array_remove'):
            node = self._array_manip_statement()
            return ASTNode('general_statement', children=[node])
        
        else:
            self._error([
                ID_T, 'show', 'if', 'while', 'for', 'try', 'todo', 'array_add', 'array_remove'
            ], "general_statement")
    
    def _id_statement_tail(self, id_name: str) -> ASTNode:
        """ 
        Parses next of id.

        Returns:
            ASTNode: AST node representing the id_statement_tail.
        """

        # Unary statement: ++ or --
        if self._match('++', '--'):
            return ASTNode('unary_statement', value=self._advance().lexeme, children=[ASTNode('id', value=id_name)])
        
        # Assignment statement: = <assignment_value>
        elif self._match('='):
            node = self._assignment_value()
            return ASTNode('assignment_statement', value=id_name, children=[node])
        
        # Function call: ( <arg_list_opt> )
        elif self._match('('):
            self._advance()
            args = self._arg_list_opt()

            if self._match(')'):
                self._advance()
            else:
                self.error([')'], 'function_call')

            # We will add 1. args
            children = []

            if args:
                children.append(ASTNode('args', children=args))

            return ASTNode('function_call', value=id_name, children=children)
        
        # Array indexing assignment: [<index>] <index_loop> = <assignment_value>
        elif self._match('['):
            indices = []

            while self._match('['):
                self._advance()

                idx = self._expr()

                indices.append(idx)

                if self._match(']'):
                    self._advance()
                else:
                    self._error([']'], 'index_loop')

            if self._match('='):
                self._advance()
                value = self._assignment_value()
        else:
            self._error(['++', '--', '=', '(', '['], 'id_statement_tail')


    def _assignment_value(self):
        self._advance()
        
        # input method
        if self._match('read'):
            self._advance()
            return ASTNode('read')
        
        # typecast method
        elif self._match('int', 'float'):
            cast_method = self._advance().lexeme
            
            FOLLOW_AFTER_TYPECAST = {
                '!=', '%', ')', '*', '**', '+', '-', '/', '//', '<', '<=', '==', '>', '>=', 'and', 'or'
            }

            if self._match('('):
                self._advance()

                expr = self._expr()

                # If after parsing an expression we don't see a comma, a closing paren,
                # or any operator that can continue the expression, produce a clearer error.
                if not self._match(*FOLLOW_AFTER_TYPECAST):
                    self._error(sorted(list(FOLLOW_AFTER_TYPECAST)), 'typecasting')


                if self._match(')'):
                    self._advance()
                else:
                    self._error([')'], 'type_casting')
                
                return ASTNode('type_casting', value=cast_method, children=[expr])
        
        elif self._match('['):
            self._advance()
            elements = self._element_list_opt()
        
            if self._match(']'):
                self._advance()
            else:
                self._error([']'], 'array_literal')

            return ASTNode('array_literal', children=elements)

        else:
            return self._expr()
    

    def _element_list_opt(self) -> List[ASTNode]:
        """
        Parse optional element_list (can be empty).
        element_list -> array_element ( , array_element )*
        """
        elements: List[ASTNode] = []
        # empty element list allowed
        if self._match(']'):
            return elements

        # at least one element
        elements.append(self._array_element())
        while self._match(','):
            self._advance()
            # allow trailing empty? (grammar says element_list -> lambda or element)
            # parse next element
            elements.append(self._array_element())

        return elements


    def _array_element(self) -> ASTNode:
        """
        Parse a single array element:
          int/float/str/bool literal | id | [ <element_list> ]
        """
        if self._match(INT_LIT_T, FLOAT_LIT_T):
            tok = self._advance()
            kind = INT_LIT_T if tok.type == INT_LIT_T else FLOAT_LIT_T
            return ASTNode(kind, value=tok.lexeme)

        elif self._match(STR_LIT_T):
            tok = self._advance()
            return ASTNode('str_literal', value=tok.lexeme)

        elif self._match('true', 'false'):
            tok = self._advance()
            return ASTNode('bool_literal', value=tok.lexeme)

        elif self._match(ID_T):
            tok = self._advance()
            node = ASTNode('id', value=tok.lexeme)
            # allow postfix (call/index) as an element
            if self._match('(', '['):
                node = self._postfix_tail(node)
            return node

        elif self._match('['):
            # nested array literal
            self._advance()
            elems = self._element_list_opt()
            if self._match(']'):
                self._advance()
                return ASTNode('array_literal', children=elems)
            else:
                self._error([']'], 'array_literal')

        else:
            self._error([INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, 'true', 'false', ID_T, '['], 'array_element')


    def _output_statement(self) -> ASTNode:
        """
        Parse a 'show' statement.

        Returns:
            ASTNode: AST node representing the output statement.
        """
        self._advance()     # consume 'show'
        if self._match(ID_T):
            return ASTNode('output_statement', children=[ASTNode('id', value=self._advance().lexeme)])
        elif self._match(STR_LIT_T):
            return ASTNode('output_statement', children=[ASTNode('str_literal', value=self._advance().lexeme)])
        else:
            self._error([ID_T, STR_LIT_T], 'output_value')


    def _conditional_statement(self) -> ASTNode:
        """
        Parse a conditional:
          if <condition> <local_statements> (elif <condition> <local_statements>)* (else <local_statements>)? close
        Returns an AST node with children: one 'if' node, zero-or-more 'elif' nodes, optional 'else' node.
        """
        # Accept being called when current token is 'if' (or, to be tolerant, 'elif')
        if self._match('if'):
            self._advance()
        else:
            self._error(['if'], 'conditional_statement')

        # condition expression
        cond = self._expr()

        # parse local statements until we hit elif / else / close
        if self._match('elif', 'else', 'close'):
            self._error(['general_statement'], 'if_block')

        if_nodes: List[ASTNode] = []

        # require one general statement
        if_nodes.append(self._general_statement())

        while not self._match('elif', 'else', 'close'):
            if_nodes.append(self._general_statement())

        if_node = ASTNode('if', children=[cond] + if_nodes)

        # zero-or-more elif blocks
        elif_nodes: List[ASTNode] = []
        while self._match('elif'):
            self._advance()
            cond_e = self._expr()

            if self._match('elif', 'else', 'close'):
                self._error(['general_statement'], 'elif_block')

            elif_body: List[ASTNode] = []

            # require 1 general statement
            elif_body.append(self._general_statement())

            while not self._match('elif', 'else', 'close'):
                elif_body.append(self._general_statement())

            elif_nodes.append(ASTNode('elif', children=[cond_e] + elif_body))

        # optional else block
        else_node: Optional[ASTNode] = None
        if self._match('else'):
            self._advance()

            if self._match('elif', 'else', 'close'):
                self._error(['general_statement'], 'else_block')

            else_body: List[ASTNode] = []

            # require one general statement
            else_body.append(self._general_statement())

            while not self._match('close'):
                else_body.append(self._general_statement())

            else_node = ASTNode('else', children=else_body)

        # final close
        if self._match('close'):
            self._advance()
        else:
            self._error(['close'], 'conditional_statement')

        # if node is already a list and we add it
        children = [if_node] + elif_nodes
        if else_node:
            children.append(else_node)
        return ASTNode('conditional_statement', children=children)


    def _looping_statement(self) -> ASTNode:
        """
        Parse for/while looping statements.
        for -> for id in range ( <expression_list> ) <local_loop_statement> close
        while -> while <condition> <local_loop_statement> close
        """
        if self._match('for'):
            self._advance()

            if not self._match(ID_T):
                self._error([ID_T], 'for_statement')

            loop_var = self._advance().lexeme

            if not self._match('in'):
                self._error(['in'], 'for_statement')

            self._advance()

            # range ( <expression_list> )
            if not self._match('range'):
                self._error(['range'], 'for_statement')

            self._advance()

            if not self._match('('):
                self._error(['('], 'range_expression')

            self._advance()

            # expression_list -> maybe empty per grammar; handle empty or expressions separated by commas
            exprs: List[ASTNode] = []

            # up to 3 range expression
            # first expression (required)
            exprs.append(self._expr())

            # optional second expression
            if self._match(','):
                self._advance()
                exprs.append(self._expr())

                # optional third expression
                if self._match(','):
                    self._advance()
                    exprs.append(self._expr())

                    # no more than 3 expressions allowed
                    if self._match(','):
                        self._error([')'], 'range_expression')
            
            if not self._match(')'):
                self._error([')'], 'range_expression')
            self._advance()

            # local loop statements until 'close'
            body: List[ASTNode] = []
            if self._match('close'):
                self._error(['general_statement', 'skip', 'stop'], 'for_body')

            while not self._match('close'):
                if self._match('skip', 'stop'):
                    tok = self._advance()
                    body.append(ASTNode('loop_control', value=tok.lexeme))
                else:
                    body.append(self._general_statement())

            if self._match('close'):
                self._advance()
            else:
                self._error(['close'], 'for_statement')

            return ASTNode('for', value=loop_var, children=exprs + body)

        elif self._match('while'):
            self._advance()
            cond = self._expr()

            body: List[ASTNode] = []
            if self._match('close'):
                self._error(['general_statement', 'skip', 'stop'], 'while_body')
            while not self._match('close'):
                if self._match('skip', 'stop'):
                    tok = self._advance()
                    body.append(ASTNode('loop_control', value=tok.lexeme))
                else:
                    body.append(self._general_statement())

            if self._match('close'):
                self._advance()
            else:
                self._error(['close'], 'while_statement')

            return ASTNode('while', children=[cond] + body)

        else:
            self._error(['for', 'while'], 'looping_statement')


    def _error_handling_statement(self) -> ASTNode:
        """
        Parse try / fail / (optional always) close block.
        try <local_statement> fail <local_statement> (always <local_statement>)? close
        """
        # try block
        if not self._match('try'):
            self._error(['try'], 'error_handling_statement')
        self._advance()

        try_body: List[ASTNode] = []
        if self._match('fail', 'always', 'close'):
            self._error(['general_statement'], 'try_block')
        while not self._match('fail', 'always', 'close'):
            try_body.append(self._general_statement())

        if not self._match('fail'):
            self._error(['fail'], 'error_handling_statement')
        self._advance()

        # fail block
        fail_body: List[ASTNode] = []
        if self._match('always', 'close'):
            self._error(['general_statement'], 'fail_block')
        while not self._match('always', 'close'):
            fail_body.append(self._general_statement())

        # optional always block
        always_node: Optional[ASTNode] = None
        if self._match('always'):
            self._advance()
            if self._match('close'):
                self._error(['general_statement'], 'always_block')
            always_body: List[ASTNode] = []
            while not self._match('close'):
                always_body.append(self._general_statement())
            always_node = ASTNode('always', children=always_body)

        # final close
        if self._match('close'):
            self._advance()
        else:
            self._error(['close'], 'error_handling_statement')

        children = [ASTNode('try', children=try_body), ASTNode('fail', children=fail_body)]
        if always_node:
            children.append(always_node)
        return ASTNode('error_handling', children=children)


    def _array_manip_statement(self) -> ASTNode:
        """
        Parse array_add(id, expr) and array_remove(id, expr)
        """
        if self._match('array_add', 'array_remove'):
            op_tok = self._advance()
            op = op_tok.type

            if not self._match('('):
                self._error(['('], 'array_manip_statement')
            self._advance()

            if not self._match(ID_T):
                self._error([ID_T], 'array_manip_statement')

            tok = self._advance()
            id_node = ASTNode('id', value=tok.lexeme)

            # allow index tail after the id (e.g., id[1][2])
            if self._match('['):
                id_node = self._postfix_tail(id_node)

            if not self._match(','):
                self._error([','], 'array_manip_statement')
            self._advance()

            expr_node = self._expr()

            if not self._match(')'):
                self._error([')'], 'array_manip_statement')
            self._advance()

            return ASTNode(op, children=[id_node, expr_node])

        self._error(['array_add', 'array_remove'], 'array_manip_statement')
