from typing import List, Optional
from src.constants.token import ID_T, INT_LIT_T, FLOAT_LIT_T, STR_LIT_T, BOOL_LIT_T, SKIP_TOKENS
from src.syntax.ast import ASTNode

class BlockStmtRules:    


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
