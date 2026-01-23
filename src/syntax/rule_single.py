"""
Single-statements parsing rules.

This module defines the `SingleStmt` mixin used by the recursive-descent
parser (`RDParser`) to parse program, general statements, argument lists,
array literals/manipulation, id-tail forms (assignment/call/index), and
return/element helpers.

Expectations:
- Mixed into a class that implements ParserCore helpers:
  - self._match(*types) -> bool
  - self._advance() -> Token
  - self._error(expected: List[str], context: str) -> raises ParseError
  - self._expr(), self._postfix_tail(), etc. provided by other mixins.

Public symbols:
- SingleStmt: mixin with statement-level parsing routines.
"""
from typing import List, Optional, TYPE_CHECKING
from src.constants.token import ID_T, INT_LIT_T, STR_LIT_T, BOOL_LIT_T, FLOAT_LIT_T, SKIP_TOKENS, Token
from src.syntax.ast import ASTNode

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class SingleStmtRules:
    """
    Mixin providing parsing rules for single/general statements and program root.

    Methods return `ASTNode` objects (see [`ASTNode`](src/syntax/ast.py)) and
    raise parse errors via `self._error(...)` when input violates grammar.
    """
    
    def _program(self: "RDParser") -> ASTNode:
        """
        Parse the top-level program structure.

        Returns:
            ASTNode: Root ASTNode representing the program.
        """
        FIRST_PROGRAM = {
            'array_add', 'array_remove', 'fn', 'for', 'id', 'if', 'show', 'todo', 'try', 'while'
        }

        if not self._match(*FIRST_PROGRAM):
            self._error([*FIRST_PROGRAM], 'program')

        funcs = self._function_statements()
        general_stmts = [self._general_statement()]

        while not self._match('EOF'):
            general_stmts.append(self._general_statement())

        children = funcs + general_stmts
        return ASTNode('program', children=children)


    def _general_statement(self: "RDParser", block_keywords: set = None) -> ASTNode:
        """
        Parse a general statement (e.g., output, control statements).

        Args:
            block_keywords: Set of keywords that are valid in the current block context (e.g., 'close', 'skip', 'stop')

        Returns:
            ASTNode: AST node representing the statement.
        """
        if block_keywords is None:
            block_keywords = set()

        # identifier-starting statement (assignment, call, unary, indexed assignment)
        if self._match(ID_T):
            id_tok = self._advance()
            node = self._id_statement_tail(id_tok, block_keywords)
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
            tok = self._advance()
            return ASTNode('general_statement', children=[self._ast_node('todo', tok)])

        # array manipulation helpers
        elif self._match('array_add', 'array_remove'):
            node = self._array_manip_statement(block_keywords)
            return ASTNode('general_statement', children=[node])

        else:
            expected = {ID_T, 'show', 'if', 'while', 'for', 'try', 'todo', 'array_add', 'array_remove'} | block_keywords
            self._error(sorted(list(expected)), "general_statement")


    def _arg_list_opt(self: "RDParser", block_keywords: set = None) -> List[ASTNode]:
        """
        Parse an optional comma-separated argument list.

        Args:
            block_keywords: Set of keywords valid in current block context

        Returns:
            List[ASTNode]: List of expression AST nodes representing arguments.
        """
        if block_keywords is None:
            block_keywords = set()
        
        args: List[ASTNode] = []

        if not self._match(')'):
            while True:
                # parse expression
                node = self._expr()
                args.append(node)

                # recompute allowed follow tokens fresh for this argument. Or else you would have trouble not resetting
                FOLLOW_AFTER_ARG = {
                    ')', ','
                } | block_keywords

                FOLLOW_AFTER_ARG = self._add_postfix_tokens(FOLLOW_AFTER_ARG, node)

                # check the next token
                if not self._match(*FOLLOW_AFTER_ARG):
                    self._error(sorted(list(FOLLOW_AFTER_ARG)), 'arg_list_opt')

                # break if no comma, otherwise consume and continue
                if not self._match(','):
                    break
                self._advance()

        return args


    def _return_opt(self: "RDParser") -> Optional[ASTNode]:
        """
        Parse an optional return statement.

        Returns:
            ASTNode | None: AST node for return statement if present.
        """
        # tokens that must always follow a ret stmt. which are all expr operators and a close token
        FOLLOW_AFTER_RET = {
            '!=', '%', '*', '**', '+', '-', '/', '//', '<', '<=', '==', '>', '>=', 'and', 'close', 'or'
        }

        if self._match('ret'):
            self._advance()

            node =  ASTNode('return_statement', children=[self._expr()])

            if not self._match(*FOLLOW_AFTER_RET):
                self._error(sorted(list(FOLLOW_AFTER_RET)), 'return_opt')

            return node
        
        return None


    def _array_element(self: "RDParser", block_keywords: set = None) -> ASTNode:
        """
        Parse a single array element (literal, id, or nested array).

        Args:
            block_keywords: Set of keywords valid in current block context

        Returns:
            ASTNode: AST node for the array element.
        """
        if block_keywords is None:
            block_keywords = set()
        if self._match(INT_LIT_T, FLOAT_LIT_T):
            tok = self._advance()
            kind = INT_LIT_T if tok.type == INT_LIT_T else FLOAT_LIT_T
            return self._ast_node(kind, tok, value=tok.lexeme)

        elif self._match(STR_LIT_T):
            tok = self._advance()
            return self._ast_node(STR_LIT_T, tok, value=tok.lexeme)

        elif self._match('true', 'false'):
            tok = self._advance()
            return self._ast_node(BOOL_LIT_T, tok, value=tok.lexeme)

        elif self._match(ID_T):
            tok = self._advance()
            return self._ast_node(ID_T, tok, value=tok.lexeme)

        elif self._match('['):
            # nested array literal
            self._advance()
            elems = self._element_list_opt(block_keywords)

            if self._match(']'):
                self._advance()
                return ASTNode('array_literal', children=elems)
            else:
                self._error([']'], 'array_literal')

        else:
            self._error([INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, 'true', 'false', ID_T, '['], 'array_element')


    def _element_list_opt(self: "RDParser", block_keywords: set = None) -> List[ASTNode]:
        """
        Parse an optional, possibly-empty list of array literal elements.

        Args:
            block_keywords: Set of keywords valid in current block context

        Returns:
            List[ASTNode]: Parsed element nodes (may be empty).
        """
        if block_keywords is None:
            block_keywords = set()
        
        elements: List[ASTNode] = []

        # empty element list allowed
        if self._match(']'):
            return elements

        # at least one element
        elements.append(self._array_element(block_keywords))

        # next of elements can be null so we need to have a proper printing
        FOLLOW_ARR_ELMNT = {
            ',', ']'
        }

        if not self._match(*FOLLOW_ARR_ELMNT):
            self._error([*FOLLOW_ARR_ELMNT], 'element_list_opt')

        while self._match(','):
            self._advance()
            # parse next element
            elements.append(self._array_element(block_keywords))

            if not self._match(*FOLLOW_ARR_ELMNT):
                self._error([*FOLLOW_ARR_ELMNT], 'element_list_opt')

        return elements


    def _output_statement(self: "RDParser") -> ASTNode:
        """
        Parse a 'show' statement.

        Returns:
            ASTNode: AST node representing the output statement.
        """
        show_tok = self._advance()

        if self._match(ID_T):
            tok = self._advance()
            return self._ast_node('output_statement', show_tok, children=[self._ast_node(ID_T, tok, value=tok.lexeme)])
        elif self._match(STR_LIT_T):
            tok = self._advance()
            return self._ast_node('output_statement', show_tok, children=[self._ast_node(STR_LIT_T, tok, value=tok.lexeme)])
        else:
            self._error([ID_T, STR_LIT_T], 'output_value')


    def _id_statement_tail(self: "RDParser", id_tok: Token, block_keywords: set = None) -> ASTNode:
        """ 
        Parses next of id.

        Args:
            id_tok: The identifier token
            block_keywords: Set of keywords valid in current block context

        Returns:
            ASTNode: AST node representing the id_statement_tail.
        """
        if block_keywords is None:
            block_keywords = set()

        # Unary statement: ++ or --
        if self._match('++', '--'):
            op_tok = self._advance()
            return self._ast_node('unary_statement', op_tok, value=op_tok.lexeme, children=[self._ast_node(ID_T, id_tok, value=id_tok.lexeme)])

        # Assignment statement: = <assignment_value>
        elif self._match('='):
            eq_tok = self._advance()        # consume '='
            node = self._assignment_value(block_keywords)   # parse RHS (no '=' consumption inside)
            return self._ast_node('assignment_statement', id_tok, value=id_tok.lexeme, children=[node])

        # Function call: ( <arg_list_opt> )
        elif self._match('('):
            self._advance()

            # arg_list_opt is nullable so we need to show complete error that includes ')'
            FOLLOW_AFTER_OPEN_PAREN = {
                '!', ')', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'
            }

            if not self._match(*FOLLOW_AFTER_OPEN_PAREN):
                self._error(sorted(list(FOLLOW_AFTER_OPEN_PAREN)), 'function_call')

            args = self._arg_list_opt(block_keywords)

            if not self._match(')'):
                self._error([')'], 'function_call')

            self._advance()

            # We will add 1. args
            children = []

            if args:
                children.append(ASTNode('args', children=args))

            return self._ast_node('function_call', id_tok, value=id_tok.lexeme, children=children)

        # Array indexing assignment: [<index>] <index_loop> = <assignment_value>
        elif self._match('['):
            indices = []

            # indexed variable array
            while self._match('['):
                self._advance()

                idx = self._index()

                indices.append(idx)

                if not self._match(']'):
                    self._error([']'], 'index_loop')

                self._advance()

            # = after indexed variable array
            if not self._match('='):
                self._error(['='], 'id_statement_tail')

            self._advance()

            value = self._assignment_value(block_keywords)

            indices_node = ASTNode('indices', children=indices)

            return self._ast_node('array_idx_assignment', id_tok, value=id_tok.lexeme, children=[indices_node, value])


        else:
            self._error(['++', '--', '=', '(', '['], 'id_statement_tail')


    def _assignment_value(self: "RDParser", block_keywords: set = None):
        if block_keywords is None:
            block_keywords = set()

        # since there are many variations, we display error full of context
        FIRST_ASSIGN_VALUE = {
            '!', '[', 'false', 'float', FLOAT_LIT_T, ID_T, 'int', INT_LIT_T, 'read', STR_LIT_T, 'true'
        }

        if not self._match(*FIRST_ASSIGN_VALUE):
            self._error([*FIRST_ASSIGN_VALUE], 'assignment_value')

        # input method
        if self._match('read'):
            tok = self._advance()
            return self._ast_node('read', tok)

        # typecast method
        elif self._match('int', 'float'):
            cast_tok = self._advance()
            cast_method = cast_tok.lexeme

            if not self._match('('):
                self._error(['('], 'assignment_value')

            self._advance()

            expr = self._expr()

            # we always need to show whole expected after expr if it errors since it is a unique
            FOLLOW_TYPECAST = { ')' }

            # get rightmost ID_T or index (ID_T[X])
            FOLLOW_TYPECAST = self._add_postfix_tokens(FOLLOW_TYPECAST, expr)

            if not self._match(')'):
                self._error(sorted(list(FOLLOW_TYPECAST)), 'assignment_value')

            self._advance()

            return self._ast_node('assignment_value', cast_tok, value=cast_method, children=[expr])

        # array literal dec
        elif self._match('['):
            bracket_tok = self._advance()

            # since _element_list_opt is nullable, we need to show this in error display
            FOLLOW_LSB = {
                '[', ']', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'
            }

            if not self._match(*FOLLOW_LSB):
                self._error([*FOLLOW_LSB], 'assignment_value')

            elements = self._element_list_opt(block_keywords)

            # this is actually kinda useless cause we check alr in the loop in elemenet_list_op
            # but just dont wanna remove it cause it looks weird. self._advance still being used
            if not self._match(']'):
                self._error([']'], 'assignment_value')

            self._advance()

            return self._ast_node('array_literal', bracket_tok, children=elements)

        else:
            # other wise, its an expr
            expr = self._expr()

            # after an expr, proper error display would be first set of gen stmt + equation ops + block keywords
            FOLLOW_ASSIGN_EXPR = self._first_general_statement() | block_keywords

            # handle id = id() and id = id[x] display proper error
            FOLLOW_ASSIGN_EXPR = self._add_postfix_tokens(FOLLOW_ASSIGN_EXPR, expr)

            # After an assignment value, we can have: EOF, block keywords, or postfix operators
            # EOF is valid when the assignment is the last statement
            if not self._match(*FOLLOW_ASSIGN_EXPR) and not self._match('EOF'):
                self._error(sorted(list(FOLLOW_ASSIGN_EXPR)), 'assignment_value')

            return expr

    def _array_manip_statement(self: "RDParser", block_keywords: set = None) -> ASTNode:
        """
        Parse array_add(id, expr) and array_remove(id, expr)
        
        Args:
            block_keywords: Set of keywords valid in current block context
        """
        if block_keywords is None:
            block_keywords = set()
        
        op_tok = self._advance()
        op = op_tok.type

        if not self._match('('):
            self._error(['('], 'array_manip_statement')
        
        self._advance()

        if not self._match(ID_T):
            self._error([ID_T], 'array_manip_statement')

        tok = self._advance()
        
        # array to manipulate id
        id_node = self._ast_node(ID_T, tok, value=tok.lexeme)

        # allow index tail after the id (e.g., id[1][2])
        if self._match('['):
            id_node = self._postfix_tail(id_node, id_tok=tok)

        # nullable after array_add(id ) & array_add(id[x] ), so we need to show proper errors
        FOLLOW_ID_AND_INDEX_RSB = {
            ',', '['
        }

        if not self._match(*FOLLOW_ID_AND_INDEX_RSB):
            self._error([*FOLLOW_ID_AND_INDEX_RSB], 'array_manip_statement')

        if not self._match(','):
            self._error([','], 'array_manip_statement')

        self._advance()

        expr_node = self._expr()

        # since expr can be null, we need to include the follow set in the error
        FOLLOW_MANIP_EXPR = {
            ')'
        } | block_keywords

        FOLLOW_MANIP_EXPR = self._add_postfix_tokens(FOLLOW_MANIP_EXPR, expr_node)

        if not self._match(*FOLLOW_MANIP_EXPR):
            self._error([*FOLLOW_MANIP_EXPR], 'array_manip_statement')

        if not self._match(')'):
            self._error([')'], 'array_manip_statement')
        self._advance()

        return self._ast_node(op, op_tok, children=[id_node, expr_node])
