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

            self._expect(self.PRED_PROGRAM, 'program')
        return nodes


    def _function_statement(self: "RDParser") -> ASTNode:
        """
        Parse a single function declaration.

        Returns:
            ASTNode: AST node representing the function with children nodes for parameters, locals, and return.
        """

        fn_tok = self._advance()  # consume 'fn' and capture token
        
        # check if next is id or else error
        self._expect_type(ID_T, 'function_statement')

        fn_name = self._advance().lexeme

        # check if next is ( or else error
        self._expect_type('(', 'function_statement')
        self._advance()

        self._expect(self.PRED_ARG_LIST_OPT, 'function_statement')

        params = self._arg_list_opt()
            
        # check if next is ) or else error
        self._expect_type(')', 'function_statement')
        self._advance()
        
        # check inside the function block
        fn_nodes = []
        predict_keywords = {'close', 'ret'}

        # require 1 local statement
        # block_keywords args is just for assignment stmt error context printing, so we stil need manual checking of predict set
        fn_nodes.append(self._general_statement(predict_keywords))
        self._expect(self.PRED_GENERAL_STMT | predict_keywords, 'function_statement')
        
        # 0 or many local statement
        while not self._match('ret', 'close'):
            # ret can be null so we need to check always to show correct error
            fn_nodes.append(self._general_statement(predict_keywords))
            self._expect(self.PRED_GENERAL_STMT | {'close', 'ret'}, 'function_statement')

        ret_node = self._return_opt()
        
        self._expect_type('close', 'function_statement')
        self._advance()

        # We will add 1. params, then 2. local_nodes, then 3. ret_nodes
        children = []

        if params:
            children.append(self._ast_node('params', fn_tok, children=params))

        children.extend(fn_nodes)

        if ret_node:
            children.append(ret_node)

        return self._ast_node('function', fn_tok, value=fn_name, children=children)


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
        # If blocks
        self._expect_type('if', 'conditional_statement')
        if_tok = self._advance() 

        # condition expression
        cond = self._expr()
        self._expect_after_expr(self.PRED_GENERAL_STMT, cond, 'if_block')

        if_nodes: List[ASTNode] = []
        predict_keywords = {'close', 'elif', 'else'}

        # require one general statement, predict keywords in assignment expr error if expr had error
        if_nodes.append(self._general_statement(predict_keywords))
        self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'if_block')

        while not self._match('elif', 'else', 'close'):
            if_nodes.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'if_block')

        if_node = self._ast_node('if', if_tok, children=[cond] + if_nodes)


        # elif blocks zero-or-more
        elif_nodes: List[ASTNode] = []
        predict_keywords = {'close', 'elif', 'else'}

        while self._match('elif'):
            elif_tok = self._advance()
            cond = self._expr()

            self._expect_after_expr(self.PRED_GENERAL_STMT, cond, 'elif_block')

            elif_body: List[ASTNode] = []

            # require 1 general statement
            elif_body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'elif_block')

            while not self._match('elif', 'else', 'close'):
                elif_body.append(self._general_statement(predict_keywords))
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'elif_block')

            elif_nodes.append(self._ast_node('elif', elif_tok, children=[cond] + elif_body))


        # optional else ast node
        else_node: Optional[ASTNode] = None
        predict_keywords = {'close'}

        if self._match('else'):
            else_tok = self._advance()
            else_body: List[ASTNode] = []   # list of general statements

            # require one general statement
            else_body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'else_block')

            while not self._match('close'):
                else_body.append(self._general_statement(predict_keywords))
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'else_block')

            # AST else node
            else_node = self._ast_node('else', else_tok, children=else_body)

        # final close, probably handled by previous expect already we add just incase.
        self._expect_type('close', 'conditional_statement')
        self._advance()

        # combine if, elif, else nodes
        children = [if_node] + elif_nodes

        if else_node:
            children.append(else_node)

        return self._ast_node('conditional_statement', if_tok, children=children)


    def _looping_statement(self: "RDParser") -> ASTNode:
        """
        Parse `for` and `while` loop statements.

        Returns:
            ASTNode: `for` node (value = loop var, children = range exprs + body)
                     or `while` node (children = cond + body).
        """
        if self._match('for'):
            self._advance()

            self._expect_type(ID_T, 'for_statement')
            loop_var = self._advance().lexeme   # advance and get variable name

            self._expect_type('in', 'for_statement')
            self._advance()

            # range ( <expression_list> )
            self._expect_type('range', 'for_statement')
            self._advance()

            self._expect_type('(', 'range_expression')
            self._advance()

            # expression_list -> maybe empty per grammar; handle empty or expressions separated by commas
            indices: List[ASTNode] = []

            # up to 3 range expression
            # first index (required)
            index = self._index()
            indices.append(index)

            # follow tokens for this argument.
            predict_keywords = { ')', ',' }
            self._expect(predict_keywords, 'range_expression')


            # optional second expression
            if self._match(','):
                self._advance()
                index = self._index()
                indices.append(index)

                # follow tokens for this argument.
                predict_keywords = { ')', ',' }
                self._expect(predict_keywords, 'range_expression')

                # optional third expression
                if self._match(','):
                    self._advance()
                    index = self._index()
                    indices.append(index)

                    # follow tokens for this argument.
                    predict_keywords = {')'}
                    self._expect(predict_keywords, 'range_expression')

            self._expect_type(')', 'range_expression')
            self._advance()

            # local loop statements until 'close'
            body: List[ASTNode] = []
            predict_keywords = {'close'}

            # expect first set of general statement
            body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'for_body')

            while not self._match('close'):
                body.append(self._general_statement(predict_keywords))
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'for_body')

            # close consumed
            for_tok = self._advance()

            return self._ast_node('for', for_tok, value=loop_var, children=indices + body)


        # while loop
        elif self._match('while'):
            while_tok = self._advance()

            body: List[ASTNode] = []
            cond = self._expr()
            predict_keywords = {'close'}

            # after parsing expr, we need to show full error context
            self._expect_after_expr(self.PRED_GENERAL_STMT, cond, 'while_statement')

            body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'while_body')

            while not self._match('close'):
                body.append(self._general_statement(predict_keywords))
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'while_body')

            # expect close, might be handled already by previous expect
            self._expect_type('close', 'while_statement')
            self._advance()

            return self._ast_node('while', while_tok, children=[cond] + body)



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

        try_tok = self._advance()
        try_body: List[ASTNode] = []
        predict_keywords = {'fail'}

        # require one general statement
        try_body.append(self._general_statement(predict_keywords))
        self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'try_block')

        while not self._match('fail'):
            try_body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'try_block')

        # fail block
        fail_tok = self._advance()
        fail_body: List[ASTNode] = []
        predict_keywords = {'always', 'close'}

        # require one general statement, pass the keywods for expr
        fail_body.append(self._general_statement(predict_keywords))
        self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'fail_block')

        while not self._match('always', 'close'):
            fail_body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'fail_block')

        # always block optional
        always_node: Optional[ASTNode] = None

        if self._match('always'):
            always_tok = self._advance()
            always_body: List[ASTNode] = []
            predict_keywords = {'close'}

            always_body.append(self._general_statement(predict_keywords))
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'always_block')

            while not self._match('close'):
                always_body.append(self._general_statement({'close'}))
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'always_block')

            always_node = self._ast_node('always', always_tok, children=always_body)


        # expect close incase. we handle expecting close in previous expects
        self._expect_type('close', 'error_handling_statement')
        self._advance()

        # combine the nodes
        children = [self._ast_node('try', try_tok, children=try_body), self._ast_node('fail', fail_tok, children=fail_body)]

        if always_node:
            children.append(always_node)

        return self._ast_node('error_handling', try_tok, children=children)
