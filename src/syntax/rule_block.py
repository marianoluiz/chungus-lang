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

    PRED_FN_GEN_STMT = {'array_add', 'array_remove', 'close', 'for', 'id', 'if', 'ret', 'show', 'todo', 'try', 'while'}

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
        block_keywords = {'close', 'ret'}

        # require 1 local statement
        # block_keywords args is just for assignment stmt error context printing, so we stil need manual checking of predict set
        fn_nodes.append(self._general_statement(block_keywords))
        self._expect(self.PRED_FN_GEN_STMT, 'function_statement')

        # 0 or many local statement
        while not self._match('ret', 'close'):
            # ret can be null so we need to check always to show correct error
            self._expect(self.PRED_FN_GEN_STMT, 'function_statement')
            fn_nodes.append(self._general_statement(block_keywords))

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

        # proper complete error after expr if it errored
        FOLLOW_EXPR_IFCOND = self._first_general_statement()
        FOLLOW_EXPR_IFCOND = self._add_postfix_tokens(FOLLOW_EXPR_IFCOND, cond)

        if not self._match(*FOLLOW_EXPR_IFCOND):
            self._error(sorted(list(FOLLOW_EXPR_IFCOND)), 'conditional_statement')

        if_nodes: List[ASTNode] = []
        block_keywords = {'close', 'elif', 'else'}

        # require one general statement
        if_nodes.append(self._general_statement(block_keywords))

        # complete next tokens for error priting
        FOLLOW_IF_GEN_STMT =  {'close', 'elif', 'else'} | self._first_general_statement()

        if not self._match(*FOLLOW_IF_GEN_STMT):
            self._error(sorted(list(FOLLOW_IF_GEN_STMT)), 'conditional_statement')


        while not self._match('elif', 'else', 'close'):
            if_nodes.append(self._general_statement(block_keywords))

            # complete next tokens for error priting
            FOLLOW_IF_GEN_STMT = {'close', 'elif', 'else'} | self._first_general_statement()

            if not self._match(*FOLLOW_IF_GEN_STMT):
                self._error(sorted(list(FOLLOW_IF_GEN_STMT)), 'conditional_statement')

        if_node = self._ast_node('if', if_tok, children=[cond] + if_nodes)


        # elif blocks zero-or-more
        elif_nodes: List[ASTNode] = []

        while self._match('elif'):
            elif_tok = self._advance()

            cond = self._expr()

            # proper complete error after expr if it errored
            FOLLOW_EXPR_ELIFCOND = self._first_general_statement()
            FOLLOW_EXPR_ELIFCOND = self._add_postfix_tokens(FOLLOW_EXPR_ELIFCOND, cond)

            if not self._match(*FOLLOW_EXPR_ELIFCOND):
                self._error(sorted(list(FOLLOW_EXPR_ELIFCOND)), 'conditional_statement')


            if self._match('elif', 'else', 'close'):
                self._error(['general_statement'], 'elif_block')

            elif_body: List[ASTNode] = []

            # require 1 general statement
            elif_body.append(self._general_statement(block_keywords))

            # complete next tokens for error priting
            FOLLOW_ELIF_GEN_STMT = {'close', 'elif', 'else'} | self._first_general_statement()

            if not self._match(*FOLLOW_ELIF_GEN_STMT):
                self._error(sorted(list(FOLLOW_ELIF_GEN_STMT)), 'conditional_statement')


            while not self._match('elif', 'else', 'close'):
                elif_body.append(self._general_statement(block_keywords))

                # complete next tokens for error priting
                FOLLOW_ELIF_GEN_STMT = {'close', 'elif', 'else'} | self._first_general_statement()

                if not self._match(*FOLLOW_ELIF_GEN_STMT):
                    self._error(sorted(list(FOLLOW_ELIF_GEN_STMT)), 'conditional_statement')

            elif_nodes.append(self._ast_node('elif', elif_tok, children=[cond] + elif_body))

        # optional else block
        else_node: Optional[ASTNode] = None

        if self._match('else'):
            else_tok = self._advance()

            else_body: List[ASTNode] = []

            # require one general statement
            else_body.append(self._general_statement(block_keywords))

            FOLLOW_ELSE_GEN_STMT = {'close'} | self._first_general_statement()

            if not self._match(*FOLLOW_ELSE_GEN_STMT):
                self._error(sorted(list(FOLLOW_ELSE_GEN_STMT)), 'conditional_statement')

            while not self._match('close'):
                else_body.append(self._general_statement(block_keywords))

                FOLLOW_ELSE_GEN_STMT = {'close'} | self._first_general_statement()

                if not self._match(*FOLLOW_ELSE_GEN_STMT):
                    self._error(sorted(list(FOLLOW_ELSE_GEN_STMT)), 'conditional_statement')

            else_node = self._ast_node('else', else_tok, children=else_body)

        # final close
        if not self._match('close'):
            self._error(['close'], 'conditional_statement')
        
        self._advance()

        # if node is already a list and we add it
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
            indices: List[ASTNode] = []

            # up to 3 range expression
            # first index (required)
            index = self._index()
            indices.append(index)

            # follow tokens for this argument.
            FOLLOW_AFTER_ARG = {
                ')', ','
            }

            # check the next token
            if not self._match(*FOLLOW_AFTER_ARG):
                self._error(sorted(list(FOLLOW_AFTER_ARG)), 'range_expression')


            # optional second expression
            if self._match(','):
                self._advance()
                index = self._index()
                indices.append(index)

                # follow tokens for this argument.
                FOLLOW_AFTER_ARG = {
                    ')', ','
                }

                # check the next token
                if not self._match(*FOLLOW_AFTER_ARG):
                    self._error(sorted(list(FOLLOW_AFTER_ARG)), 'range_expression')

                # optional third expression
                if self._match(','):
                    self._advance()
                    index = self._index()
                    indices.append(index)

                    # follow tokens for this argument.
                    FOLLOW_AFTER_ARG = {
                        ')'
                    }

                    # check the next token
                    if not self._match(*FOLLOW_AFTER_ARG):
                        self._error(sorted(list(FOLLOW_AFTER_ARG)), 'range_expression')


                    # no more than 3 expressions allowed
                    if self._match(','):
                        self._error([')'], 'range_expression')
            
            if not self._match(')'):
                self._error([')'], 'range_expression')

            self._advance()

            # local loop statements until 'close'
            body: List[ASTNode] = []
            # loop_block_keywords
            loop_block_keywords = {'close'}

            FIRST_LOOP_ITEM = self._first_general_statement()
            FOLLOW_LOOP_ITEM = {'close'} | FIRST_LOOP_ITEM

            # error to not have at least 1 gen stmt
            if not self._match(*FIRST_LOOP_ITEM):
                self._error(sorted(list(FIRST_LOOP_ITEM)), 'for_body')

            while not self._match('close'):
                # error printing
                body.append(self._general_statement(loop_block_keywords))

                # error to have close
                if not self._match(*FOLLOW_LOOP_ITEM):
                    self._error(sorted(list(FOLLOW_LOOP_ITEM)), 'for_body')


            # close consumed
            for_tok = self._advance()

            return self._ast_node('for', for_tok, value=loop_var, children=indices + body)


        # while loop

        elif self._match('while'):
            while_tok = self._advance()
            cond = self._expr()

            body: List[ASTNode] = []
            loop_block_keywords = {'close'}
            FIRST_LOOP_ITEM = self._first_general_statement()
            FOLLOW_LOOP_ITEM = {'close'} | FIRST_LOOP_ITEM

            # after parsing expr, we need to show full error context
            FIRST_LOOP_ITEM = self._add_postfix_tokens(FIRST_LOOP_ITEM, cond)

            # error to have skip and stop
            if not self._match(*FIRST_LOOP_ITEM):
                self._error(sorted(list(FIRST_LOOP_ITEM)), 'while_body')

            while not self._match('close'):
                body.append(self._general_statement(loop_block_keywords))

                # error to have skip and stop and close
                if not self._match(*FOLLOW_LOOP_ITEM):
                    self._error(sorted(list(FOLLOW_LOOP_ITEM)), 'while_body')

            if self._match('close'):
                self._advance()
            else:
                self._error(['close'], 'while_statement')

            return self._ast_node('while', while_tok, children=[cond] + body)

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

        try_tok = self._advance()


        try_body: List[ASTNode] = []
        try_block_keywords = {'fail'}

        # require one general statement
        try_body.append(self._general_statement(try_block_keywords))

        # check proper follow set after general statement
        FOLLOW_TRY_GEN_STMT = try_block_keywords | self._first_general_statement()

        while not self._match('fail'):
            if not self._match(*FOLLOW_TRY_GEN_STMT):
                self._error(sorted(list(FOLLOW_TRY_GEN_STMT)), 'try_block')

            try_body.append(self._general_statement(try_block_keywords))

        # fail block
        fail_tok = self._advance()

        fail_body: List[ASTNode] = []
        
        fail_block_keywords = {'always', 'close'}


        # check proper follow set after general statement
        FOLLOW_FAIL_GEN_STMT = fail_block_keywords | self._first_general_statement()


        # require one general statement, pass the keywrods for expr
        fail_body.append(self._general_statement(fail_block_keywords))

        while not self._match('always', 'close'):
            if not self._match(*FOLLOW_FAIL_GEN_STMT):
                self._error(sorted(list(FOLLOW_FAIL_GEN_STMT)), 'fail_block')

            fail_body.append(self._general_statement(fail_block_keywords))

        # optional always block
        always_node: Optional[ASTNode] = None

        if self._match('always'):
            always_tok = self._advance()

            always_body: List[ASTNode] = []

            # check proper follow set after general statement
            FOLLOW_ALWYS_GEN_STMT = {'close'} | self._first_general_statement()

            always_body.append(self._general_statement({'close'}))

            while not self._match('close'):
                # check follow set 
                if not self._match(*FOLLOW_ALWYS_GEN_STMT):
                    self._error(sorted(list(FOLLOW_ALWYS_GEN_STMT)), 'always_block')

                always_body.append(self._general_statement({'close'}))


            always_node = self._ast_node('always', always_tok, children=always_body)

        # final close
        if not self._match('close'):
            self._error(['close'], 'error_handling_statement')

        self._advance()

        children = [self._ast_node('try', try_tok, children=try_body), self._ast_node('fail', fail_tok, children=fail_body)]

        if always_node:
            children.append(always_node)

        return self._ast_node('error_handling', try_tok, children=children)
