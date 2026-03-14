from typing import List, Optional, TYPE_CHECKING
from src.constants.token import Token, SKIP_TOKENS, ID_T, STR_LIT_T, BOOL_LIT_T, FLOAT_LIT_T, INT_LIT_T
from src.constants.ast import ASTNode

# helps editor understand "self" in mixin methods is an RDParser instance
if TYPE_CHECKING: from src.syntax.rd_parser import RDParser


class BlockStmtRules():    
    """
    Block-level statements parsing rules.

    Used by (`RDParser`) to parse block-introducing constructs like `fn`, `if/elif/else`, `for`, `while`,
    and enforce explicit `close` termination.
    """

    def _function_blocks(self: "RDParser") -> List[ASTNode]:
        """
        Parse a sequence of function declarations.

        ```
        <function_blocks>
            -> <function_block> <function_blocks>
            -> λ
        ```

        Returns:
            List[ASTNode]
        """

        nodes = []
        while self._match('fn'):
            nodes.append(self._function_block())

            self._expect(self.PRED_PROGRAM, 'program')
        return nodes


    def _function_block(self: "RDParser") -> ASTNode:
        """
        Parse a single function declaration.

        ```
        <function_block>
            -> fn id ( <param_list_opt> ) : <local_statement> <return_opt> close
        
        <local_statement>
            -> <general_statement> <local_statement_tail>
        
        <local_statement_tail>
            -> <general_statement> <local_statement_tail>
            -> λ
        ```

        Returns:
            ASTNode
        """

        fn_tok = self._advance()  # consume 'fn' and capture token
        
        # check if next is id or else error
        self._expect_type(ID_T, 'function_block')

        fn_name = self._advance().lexeme

        # check if next is ( or else error
        self._expect_type('(', 'function_block')
        self._advance()

        self._expect({')', ID_T}, 'function_block')

        params = self._param_list_opt()

        # check if next is ) or else error, this is checked already in arg_list_opt since we need expr tokens
        self._expect_type(')', 'function_block')
        self._advance()

        # require colon after function header
        self._expect_type(':', 'function_block')
        self._advance()

        # check inside the function block
        fn_nodes = []
        predict_keywords = {'close', 'ret'}

        # require 1 local statement
        # block_keywords args is just for assignment stmt error context printing, so we stil need manual checking of predict set
        fn_nodes.append(self._general_statement())
        self._expect(self.PRED_GENERAL_STMT | predict_keywords, 'function_block')

        # 0 or many local statement
        while not self._match('ret', 'close'):
            # ret can be null so we need to check always to show correct error
            fn_nodes.append(self._general_statement())
            self._expect(self.PRED_GENERAL_STMT | predict_keywords, 'function_block')

        ret_node = self._return_opt()
        
        self._expect_type('close', 'function_block')
        self._advance()

        # We will add 1. params, then 2. local_nodes, then 3. ret_nodes
        children = []

        if params:
            children.append(self._ast_node('params', fn_tok, children=params))

        children.extend(fn_nodes)

        if ret_node:
            children.append(ret_node)

        return self._ast_node('function', fn_tok, value=fn_name, children=children)


    def _conditional_block(self: "RDParser") -> ASTNode:
        """
        Parse an if/elif/else conditional block.

        ```
        <conditional_block>
            -> <if_block> <elif_block> <else_block> close

        <if_block>
            -> if <condition> : <local_statement>

        <elif_block>
            -> elif <condition> : <local_statement> <elif_block>
            -> λ

        <else_block>
            -> else : <local_statement>
            -> λ
        
        <condition>
            -> <expr>
        ```

        Returns:
            ASTNode
        """
        # If blocks
        self._expect_type('if', 'conditional_block')
        if_tok = self._advance() 

        # condition expression
        cond = self._expr()
        self._expect_after_expr({':'}, cond, 'if_block')

        # backup required
        self._expect_type(':', 'if_block')
        self._advance()

        if_nodes: List[ASTNode] = []
        predict_keywords = {'close', 'elif', 'else'}

        # require one general statement, predict keywords in assignment expr error if expr had error
        if_nodes.append(self._general_statement())
        self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'if_block')

        while not self._match('elif', 'else', 'close'):
            if_nodes.append(self._general_statement())
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'if_block')

        if_node = self._ast_node('if', if_tok, children=[cond] + if_nodes)


        # elif blocks zero-or-more
        elif_nodes: List[ASTNode] = []
        predict_keywords = {'close', 'elif', 'else'}

        while self._match('elif'):
            elif_tok = self._advance()
            cond = self._expr()

            self._expect_after_expr({':'}, cond, 'elif_block')
            self._expect_type(':', 'elif_block')
            self._advance()

            elif_body: List[ASTNode] = []

            # require 1 general statement
            elif_body.append(self._general_statement())
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'elif_block')

            while not self._match('elif', 'else', 'close'):
                elif_body.append(self._general_statement())
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'elif_block')

            elif_nodes.append(self._ast_node('elif', elif_tok, children=[cond] + elif_body))


        # optional else ast node
        else_node: Optional[ASTNode] = None
        predict_keywords = {'close'}

        if self._match('else'):
            else_tok = self._advance()
            self._expect_type(':', 'else_block')
            self._advance()
            else_body: List[ASTNode] = []   # list of general statements

            # require one general statement
            else_body.append(self._general_statement())
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'else_block')

            while not self._match('close'):
                else_body.append(self._general_statement())
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'else_block')

            # AST else node
            else_node = self._ast_node('else', else_tok, children=else_body)

        # final close, probably handled by previous expect already we add just incase.
        self._expect_type('close', 'conditional_block')
        self._advance()

        # combine if, elif, else nodes
        children = [if_node] + elif_nodes

        if else_node:
            children.append(else_node)

        return self._ast_node('conditional_block', if_tok, children=children)


    def _looping_block(self: "RDParser") -> ASTNode:
        """
        Parse a for/while loop statement.

        ```
        <looping_block>
            -> <for_block>
            -> <while_block>

        <for_block>
            -> for id in <range_expression> : <local_statement> close

        <while_block>
            -> while <condition> : <local_statement> close
            
        <range_expression>
            -> range ( <range_list> )
        
        <range_list>
            -> <index> <range_tail_1>
        
        <range_tail_1>
            -> , <index> <range_tail_2>
            -> λ
        
        <range_tail_2>
            -> , <index>
            -> λ
        ```

        Returns:
            ASTNode
        """

        if self._match('for'):
            self._advance()

            self._expect_type(ID_T, 'for_block')
            loop_var = self._advance().lexeme   # advance and get variable name

            self._expect_type('in', 'for_block')
            self._advance()

            # range ( <expression_list> )
            self._expect_type('range', 'for_block')
            self._advance()

            self._expect_type('(', 'range_expression')
            self._advance()

            # expression_list -> maybe empty per grammar; handle empty or expressions separated by commas
            indices: List[ASTNode] = []

            # up to 3 range expression

            # <range_list> -> <expr> <range_tail_1>
            # first expr (required)
            expr_node = self._expr()
            indices.append(expr_node)

            # follow tokens for this argument.
            predict_keywords = { ')', ',' }
            self._expect_after_expr(predict_keywords, expr_node, 'range_expression')

            # optional second expression
            # <range_tail_1>
            #     -> , <expr> <range_tail_2>
            #     -> λ
            if self._match(','):
                self._advance()
                expr_node = self._expr()
                indices.append(expr_node)

                # follow tokens for this argument.
                predict_keywords = { ')', ',' }
                self._expect_after_expr(predict_keywords, expr_node, 'range_expression')

                # optional third expression
                #  <range_tail_2>
                #       -> , <expr>
                #       -> λ
                if self._match(','):
                    self._advance()
                    expr_node = self._expr()
                    indices.append(expr_node)

                    # follow tokens for this argument.
                    predict_keywords = {')'}
                    self._expect_after_expr(predict_keywords, expr_node, 'range_expression')

            self._expect_type(')', 'range_expression')
            self._advance()

            # require colon after for header
            self._expect_type(':', 'for_statement')
            self._advance()

            # local loop statements until 'close'
            body: List[ASTNode] = []
            predict_keywords = {'close'}

            # expect first set of general statement
            body.append(self._general_statement())
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'for_body')

            while not self._match('close'):
                body.append(self._general_statement())
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
            self._expect_after_expr({':'}, cond, 'while_block')
            self._expect_type(':', 'while_block')
            self._advance()

            body.append(self._general_statement())
            self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'while_block')

            while not self._match('close'):
                body.append(self._general_statement())
                self._expect(predict_keywords | self.PRED_GENERAL_STMT, 'while_block')

            # expect close, might be handled already by previous expect
            self._expect_type('close', 'while_block')
            self._advance()

            return self._ast_node('while', while_tok, children=[cond] + body)

