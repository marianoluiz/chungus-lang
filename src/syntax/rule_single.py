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
    
    PRED_GENERAL_STMT = {'array_add','array_remove','for', ID_T,'if','show','todo','try','while'}
    PRED_PROGRAM = PRED_GENERAL_STMT | {'fn'}
    PRED_ID_STMT_TAIL = {'++', '--', '=', '(', '['}
    PRED_ASSIGN_VALUE = {'!', '[', 'false', 'float', FLOAT_LIT_T, ID_T, 'int', INT_LIT_T, 'read', STR_LIT_T, 'true'}
    PRED_ELEMENT_LIST = {'[', ']', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'}
    PRED_ARRAY_ELEMENT = {'[', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'}
    PRED_ARRAY_TAIL = {',', ']'}
    PRED_ARG_LIST_OPT = {'!', ')', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'}
    PRED_ARG_ELEMENT_TAIL = {')', ','}
    PRED_INDEX = {INT_LIT_T, ID_T}
    PRED_ARR_INDEX_ASSIGN_INDEX_LOOP = {'=', '['}
    PRED_ARR_MANIP_INDEX_LOOP = {',', '['} 


    def _program(self: "RDParser") -> ASTNode:
        """
        Parse the top-level program structure.

        Returns:
            ASTNode: Root ASTNode representing the program.
        """

        self._expect(self.PRED_PROGRAM, 'program')

        funcs = self._function_statements()

        # one general statement
        general_stmts = [self._general_statement()]

        # many optional general statement
        while not self._match('EOF'):
            general_stmts.append(self._general_statement())

        children = funcs + general_stmts
        return ASTNode('program', children=children)


    def _general_statement(self: "RDParser", block_keywords: set = None, allow_eof=False) -> ASTNode:
        """
        Parse a general statement (e.g., output, control statements).

        Args:
            block_keywords: Set of keywords that are valid in the current block context (e.g., 'close', 'skip', 'stop')

        Returns:
            ASTNode: AST node representing the statement.
        """
        if block_keywords is None:
            block_keywords = set()

        self._expect(self.PRED_GENERAL_STMT, 'general_statement')

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

        # looping (for / while ... close)
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

        # array_add ( id <index_loop> , <expr> )
        elif self._match('array_add'):
            node = self._array_add_statement()
            return ASTNode('general_statement', children=[node])

        # array_remove ( id <index_loop>, <index> )
        elif self._match('array_remove'):
            node = self._array_remove_statement()
            return ASTNode('general_statement', children=[node])


    def _arg_list_opt(self: "RDParser") -> List[ASTNode]:
        """
        Parse an optional comma-separated argument list.

        Args:
            block_keywords: Set of keywords valid in current block context

        Returns:
            List[ASTNode]: List of expression AST nodes representing arguments.
        """

        self._expect(self.PRED_ARG_LIST_OPT, '_arg_list_opt')

        args: List[ASTNode] = []

        if not self._match(')'):
            while True:
                # parse expression
                expr = self._expr()
                args.append(expr)

                # after parsing expr, we need to show full error context
                # recompute allowed follow tokens fresh for this argument. Or else you would have trouble not resetting
                self._expect_after_expr(self.PRED_ARG_ELEMENT_TAIL, expr, 'arg_list_opt')

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

        if self._match('ret'):
            self._advance()
            expr = self._expr()

            self._expect_after_expr({'close'}, expr, 'return_opt')

            node =  ASTNode('return_statement', children=[expr])
            return node
        
        return None


    def _array_element(self: "RDParser") -> ASTNode:
        """
        Parse a single array element (literal, id, or nested array).

        Args:
            block_keywords: Set of keywords valid in current block context

        Returns:
            ASTNode: AST node for the array element.
        """

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
            elems = self._element_list_opt()
            
            # backup expect to be ]
            self._expect_type(']', 'array_literal')
            self._advance()

            return ASTNode('array_literal', children=elems)


        else:
            self._error(self.PRED_ARRAY_ELEMENT, 'array_element')


    def _element_list_opt(self: "RDParser") -> List[ASTNode]:
        """
        Parse an optional, possibly-empty list of array literal elements.

        Args:
            block_keywords: Set of keywords valid in current block context

        Returns:
            List[ASTNode]: Parsed element nodes (may be empty).
        """

        self._expect(self.PRED_ELEMENT_LIST, 'element_list_opt')

        elements: List[ASTNode] = []

        # empty element list allowed
        if self._match(']'):
            return elements

        # at least one element
        elements.append(self._array_element())
        self._expect(self.PRED_ARRAY_TAIL, 'element_list_opt')

        while self._match(','):
            self._advance()
            # parse next element
            elements.append(self._array_element())

            self._expect(self.PRED_ARRAY_TAIL, 'element_list_opt')

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


    def _id_statement_tail(self: "RDParser", id_tok: Token, block_keywords: set = None, allow_eof = False) -> ASTNode:
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

        self._expect(self.PRED_ID_STMT_TAIL, 'id_statement_tail')

        # Unary statement: ++ or --
        if self._match('++', '--'):
            op_tok = self._advance()
            return self._ast_node('unary_statement', op_tok, value=op_tok.lexeme, children=[self._ast_node(ID_T, id_tok, value=id_tok.lexeme)])

        # Assignment statement: = <assignment_value>
        elif self._match('='):
            self._advance()
            node = self._assignment_value(block_keywords)   # parse RHS (no '=' consumption inside)
            return self._ast_node('assignment_statement', id_tok, value=id_tok.lexeme, children=[node])

        # Function call: ( <arg_list_opt> )
        elif self._match('('):
            self._advance()

            args = self._arg_list_opt()

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

                self._expect_type(']', 'index_loop')
                self._advance()

            # = after indexed variable array, we need to print whole context
            self._expect(self.PRED_ARR_INDEX_ASSIGN_INDEX_LOOP, 'index_loop')

            # consume equal
            self._advance()

            value = self._assignment_value(block_keywords, allow_eof)

            # create node of indices for ast
            indices_node = ASTNode('indices', children=indices)

            return self._ast_node('array_idx_assignment', id_tok, value=id_tok.lexeme, children=[indices_node, value])


    def _assignment_value(self: "RDParser", block_keywords: set = None, allow_eof = False):
        if block_keywords is None:
            block_keywords = set()

        self._expect(self.PRED_ASSIGN_VALUE, 'assignment_value')

        # input method
        if self._match('read'):
            tok = self._advance()
            return self._ast_node('read', tok)

        # typecast method
        elif self._match('int', 'float'):
            cast_tok = self._advance()
            cast_method = cast_tok.lexeme

            if not self._match('('):
                self._expect_type('(', 'assignment_value')

            self._advance()

            expr = self._expr()

            # we always need to show whole expected after expr if it errors since it is a unique
            # this mainly checks ')' after expr but we include the whole context
            self._expect_after_expr({ ')' }, expr, 'assignment_value', block_keywords=block_keywords, allow_eof=False)
            self._advance()

            return self._ast_node('assignment_value', cast_tok, value=cast_method, children=[expr])

        # array literal dec
        elif self._match('['):
            bracket_tok = self._advance()

            self._expect(self.PRED_ELEMENT_LIST, 'assignment_value')

            elements = self._element_list_opt()

            # this is actually kinda useless cause we check alr predict set in the loop in elemenet_list_op
            self._expect_type(']', 'assignment_value')
            self._advance()

            return self._ast_node('array_literal', bracket_tok, children=elements)

        else:
            # other wise, its an expr
            expr = self._expr()

            # if block_keywords empty, then we're at top level, so that means EOF is a valid next token
            allow_eof = (len(block_keywords) == 0)

            # after an expr, proper error display would be first set of gen stmt + equation ops + block keywords
            self._expect_after_expr(self.PRED_GENERAL_STMT | block_keywords, expr, 'assignment_value', allow_eof=allow_eof)

            return expr


    def _array_add_statement(self: "RDParser") -> ASTNode:
        """
        Parse array_add(id, expr) and array_remove(id, expr)
        
        Args:
            block_keywords: Set of keywords valid in current block context
        """

        op_tok = self._advance()
        op = op_tok.type

        self._expect_type('(', 'array_add_statement')        
        self._advance()

        self._expect_type(ID_T, 'array_add_statement')        
        tok = self._advance()
        
        # create ast node with id name
        id_node = self._ast_node(ID_T, tok, value=tok.lexeme)

        # allow index tail after the id (e.g., id[1][2])
        if self._match('['):
            id_node = self._postfix_tail(id_node, id_tok=tok)

        # Expect ,
        self._expect(self.PRED_ARR_MANIP_INDEX_LOOP, 'array_add_statement')
        self._advance()

        expr_node = self._expr()

        # expect ) otherwise print whole error context
        self._expect_after_expr({')'}, expr_node, 'array_add_statement')
        self._advance()

        return self._ast_node(op, op_tok, children=[id_node, expr_node])


    def _array_remove_statement(self: "RDParser"):
        """
        Parse array_remove(id, expr) and array_remove(id, expr)
        
        Args:
            block_keywords: Set of keywords valid in current block context
        """

        op_tok = self._advance()
        op = op_tok.type

        self._expect_type('(', 'array_add_statement')        
        self._advance()

        self._expect_type(ID_T, 'array_add_statement')        
        tok = self._advance()
        
        # create ast node with id name
        id_node = self._ast_node(ID_T, tok, value=tok.lexeme)

        # allow index tail after the id (e.g., id[1][2])
        if self._match('['):
            id_node = self._postfix_tail(id_node, id_tok=tok)

        # Expect ,
        self._expect(self.PRED_ARR_MANIP_INDEX_LOOP, 'array_add_statement')
        self._advance()

        index_node = self._index()

        # expect ) otherwise print whole error context
        self._expect({')'}, 'array_remove_statement')
        self._advance()

        return self._ast_node(op, op_tok, children=[id_node, index_node])
