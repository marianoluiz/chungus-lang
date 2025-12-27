"""
Block statement parsing rules.

This module provides BlockStmtRules, a mixin containing the top-level block and
statement parsing routines used by the recursive-descent parser `RDParser`.

The mixin expects to be mixed into a class that implements the ParserCore API:
- self._match(*types) -> bool
- self._advance() -> Token
- self._error(expected: List[str], context: str) -> raises ParseError
- self._expr(), self._general_statement(), etc. provided by other rule mixins.

Public symbols:
- BlockStmtRules: mixin with functions to parse function declarations, conditionals,
  loops and try/fail blocks.
"""
from typing import List, Optional, TYPE_CHECKING
from src.constants.token import Token, SKIP_TOKENS, ID_T, STR_LIT_T, BOOL_LIT_T, FLOAT_LIT_T, INT_LIT_T
from src.syntax.ast import ASTNode

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class BlockStmtRules():    
    """
    Statement parsing mixin that implements function/conditional/loop/error-block rules.

    Usage:
        class RDParser(ParserCore, ExprRules, BlockStmtRules):
            ...
    The methods raise parse errors via self._error(...) when encountering invalid input.
    """

    def _function_statements(self: "RDParser") -> List[ASTNode]:
        """
        Parse a sequence of function declarations.

        Returns:
            List[ASTNode]: List of function AST nodes.
        """
        nodes = []
        while self._match('fn'):
            nodes.append(self._function_statement())
        return nodes


    def _function_statement(self: "RDParser") -> ASTNode:
        """
        Parse a single function declaration.

        Returns:
            ASTNode: AST node representing the function with children nodes for parameters, locals, and return.
        """

        self._advance()  # consume 'fn'
    
        # check if next is id or else error
        if not self._match(ID_T):
            self._error([ID_T], 'function_name')

        fn_name = self._advance().lexeme

        # check if next is ( or else error
        if not self._match('('):
            self._error(['('], 'function_declaration')

        self._advance()

        # this can be null so we track the follow set of id to show more complete error
        FOLLOW_FUNC_ID = {
            '!', '(', ')', 'false', FLOAT_LIT_T, ID_T, INT_LIT_T, STR_LIT_T, 'true'
        }

        if not self._match(*FOLLOW_FUNC_ID):
            self._error(sorted(list(FOLLOW_FUNC_ID)), 'function_declaration')

        params = self._arg_list_opt()
            
        # check if next is ) or else error
        if not self._match(')'):
            self._error([')'], 'function_declaration')

        self._advance()

        # check inside the function block
        fn_nodes = []

        # require 1 local statement
        fn_nodes.append(self._general_statement())
        
        # ret can be null so we need to check always to show correct error
        FOLLOW_FUNC_GEN_STMT = {
            'array_add', 'array_remove', 'close', 'for', 'id', 'if', 'ret', 'show', 'todo', 'try', 'while'
        }

        # 0 or many local statement
        while not self._match('ret', 'close'):
            
            # ret can be null so we need to check always to show correct error
            if not self._match(*FOLLOW_FUNC_GEN_STMT):
                self._error(sorted(list(FOLLOW_FUNC_GEN_STMT)), 'function_body')

            fn_nodes.append(self._general_statement())

        ret_node = self._return_opt()

        if not self._match('close'):
            self._error(['close'], 'function_declaration')

        self._advance()

        # We will add 1. params, then 2. local_nodes, then 3. ret_nodes
        children = []

        if params:
            children.append(ASTNode('params', children=params))

        children.extend(fn_nodes)

        if ret_node:
            children.append(ret_node)

        return ASTNode('function', value=fn_name, children=children)


    def _conditional_statement(self: "RDParser") -> ASTNode:
        """
        Parse an if/elif/else conditional block.

        Grammar (informal):
            if <expr> <general_statement>+ (elif <expr> <general_statement>+)* (else <general_statement>+)? close

        Returns:
            ASTNode: `conditional_statement` node containing:
                - one `if` node (cond + body)
                - zero-or-more `elif` nodes (cond + body)
                - optional `else` node (body)
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


    def _looping_statement(self: "RDParser") -> ASTNode:
        """
        Parse `for` and `while` loop statements.

        Returns:
            ASTNode: `for` node (value = loop var, children = range exprs + body)
                     or `while` node (children = cond + body).
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


    def _error_handling_statement(self: "RDParser") -> ASTNode:
        """
        Parse try/fail/(optional)always blocks.

        Grammar (informal):
            try <general_statement>+ fail <general_statement>+ (always <general_statement>+)? close

        Returns:
            ASTNode: `error_handling` node with children:
                - `try` (children = try body)
                - `fail` (children = fail body)
                - optional `always` (children = always body)
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
