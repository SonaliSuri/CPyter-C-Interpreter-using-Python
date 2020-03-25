from ..lexer_analyzer.token_type import *
from .syntax_tree import *
from ..utils.utils import restorable


class Parser(object):
    def __init__(self, lexer):
        self.lexer = lexer
        self.current_token = self.lexer.get_next_token

    def error(self, message):
        raise SyntaxError(message)

    def use(self, token_type):

        if self.current_token.type == token_type:
            self.current_token = self.lexer.get_next_token
        else:
            self.error(
                'Expected token <{}> but found <{}> at line {}.'.format(
                    token_type, self.current_token.type, self.lexer.line
                )
            )

    def program(self):
        root = Program(
            declarations=self.declarations(),
            line=self.lexer.line

        )
        return root

    def declarations(self):
        declarations = []

        while self.current_token.type in [CHAR, FLOAT, DOUBLE, INT, HASH, VOID]:
            if self.current_token.type == HASH:
                declarations.append(self.include_library())
            elif self.check_function():
                declarations.append(self.function_declaration())
            else:
                declarations.extend(self.declaration_list())
        return declarations

    def include_library(self):
        self.use(HASH)
        token = self.current_token
        if token.value != 'include':
            self.error(
                'Expected token "include" but found {} at line {}.'.format(
                    token.value, self.lexer.line
                )
            )

        self.use(ID)
        self.use(LT_OP)
        token = self.current_token
        self.use(ID)
        self.use(DOT)
        extension = self.current_token
        if extension.value != 'h':
            self.error(
                'You can include only *.h files [line {}]'.format(self.lexer.line)
            )
        self.use(ID)
        self.use(GT_OP)
        return IncludeLibrary(
            library_name=token.value,
            line=self.lexer.line
        )

    @restorable
    def check_function(self):
        self.use(self.current_token.type)
        self.use(ID)
        return self.current_token.type == LPAREN

    def function_declaration(self):
        type_node = self.type_spec()
        func_name = self.current_token.value
        self.use(ID)
        self.use(LPAREN)
        params = self.parameters()
        self.use(RPAREN)
        return FunctionDeclaration(
            type_node=type_node,
            func_name=func_name,
            params=params,
            body=self.function_body(),
            line=self.lexer.line
        )

    def function_body(self):
        result = []
        self.use(LBRACKET)
        while self.current_token.type != RBRACKET:
            if self.current_token.type in (CHAR, INT, FLOAT, DOUBLE):
                result.extend(self.declaration_list())
            else:
                result.append(self.statement())
        self.use(RBRACKET)
        return FunctionBody(
            children=result,
            line=self.lexer.line
        )

    def parameters(self):

        nodes = []
        if self.current_token.type != RPAREN:
            nodes = [Param(
                type_node=self.type_spec(),
                var_node=self.variable(),
                line=self.lexer.line
            )]
            while self.current_token.type == COMMA:
                self.use(COMMA)
                nodes.append(Param(
                    type_node=self.type_spec(),
                    var_node=self.variable(),
                    line=self.lexer.line
                ))
        return nodes

    def declaration_list(self):
        result = self.declaration()
        while self.current_token.type == (CHAR, INT, FLOAT, DOUBLE):
            result.extend(self.declaration())
        return result

    def declaration(self):
        result = list()
        type_node = self.type_spec()
        for node in self.init_declarator_list():
            if isinstance(node, Var):
                result.append(VarDeclaration(
                    type_node=type_node,
                    var_node=node,
                    line=self.lexer.line
                ))
            else:
                result.append(node)
        self.use(SEMICOLON)
        return result

    def init_declarator_list(self):
        result = list()
        result.extend(self.init_declarator())
        while self.current_token.type == COMMA:
            self.use(COMMA)
            result.extend(self.init_declarator())
        return result

    def init_declarator(self):
        var = self.variable()
        result = list()
        result.append(var)
        if self.current_token.type == ASSIGN:
            token = self.current_token
            self.use(ASSIGN)
            result.append(Assign(
                left=var,
                op=token,
                right=self.assignment_expression(),
                line=self.lexer.line
            ))
        return result

    def statement(self):
        if self.check_iteration_statement():
            return self.iteration_statement()
        elif self.check_selection_statement():
            return self.selection_statement()
        elif self.check_jump_statement():
            return self.jump_statement()
        elif self.check_compound_statement():
            return self.compound_statement()
        return self.expression_statement()

    @restorable
    def check_compound_statement(self):
        return self.current_token.type == LBRACKET

    def compound_statement(self):
        result = []
        self.use(LBRACKET)
        while self.current_token.type != RBRACKET:
            if self.current_token.type in (CHAR, INT, FLOAT, DOUBLE):
                result.extend(self.declaration_list())
            else:
                result.append(self.statement())
        self.use(RBRACKET)
        return CompoundStatement(
            children=result,
            line=self.lexer.line
        )

    @restorable
    def check_jump_statement(self):
        return self.current_token.type in (RETURN, BREAK, CONTINUE)

    def jump_statement(self):
        if self.current_token.type == RETURN:
            self.use(RETURN)
            expression = self.empty()
            if self.current_token.type != SEMICOLON:
                expression = self.expression()
            self.use(SEMICOLON)
            return ReturnStmt(
                expression=expression,
                line=self.lexer.line
            )
        elif self.current_token.type == BREAK:
            self.use(BREAK)
            self.use(SEMICOLON)
            return BreakStatement(
                line=self.lexer.line
            )

        elif self.current_token.type == CONTINUE:
            self.use(CONTINUE)
            self.use(SEMICOLON)
            return ContinueStatement(
                line=self.lexer.line
            )

    @restorable
    def check_selection_statement(self):
        return self.current_token.type == IF

    def selection_statement(self):
        if self.current_token.type == IF:
            self.use(IF)
            self.use(LPAREN)
            condition = self.expression()
            self.use(RPAREN)
            tstatement = self.statement()
            fstatement = self.empty()
            if self.current_token.type == ELSE:
                self.use(ELSE)
                fstatement = self.statement()
            return IfStatement(
                condition=condition,
                tbody=tstatement,
                fbody=fstatement,
                line=self.lexer.line
            )

    @restorable
    def check_iteration_statement(self):
        return self.current_token.type in (WHILE, DO, FOR)

    def iteration_statement(self):
        if self.current_token.type == WHILE:
            self.use(WHILE)
            self.use(LPAREN)
            expression = self.expression()
            self.use(RPAREN)
            statement = self.statement()
            return WhileStatement(
                condition=expression,
                body=statement,
                line=self.lexer.line
            )
        elif self.current_token.type == DO:
            self.use(DO)
            statement = self.statement()
            self.use(WHILE)
            self.use(LPAREN)
            expression = self.expression()
            self.use(RPAREN)
            self.use(SEMICOLON)
            return DoWhileStatement(
                condition=expression,
                body=statement,
                line=self.lexer.line
            )
        else:
            self.use(FOR)
            self.use(LPAREN)
            setup = self.expression_statement()
            condition = self.expression_statement()
            increment = NoOp(line=self.lexer.line)
            if self.current_token.type != RPAREN:
                increment = self.expression()
            self.use(RPAREN)
            statement = self.statement()
            return ForStatement(
                setup=setup,
                condition=condition,
                increment=increment,
                body=statement,
                line=self.lexer.line
            )

    def expression_statement(self):
        node = None
        if self.current_token.type != SEMICOLON:
            node = self.expression()
        self.use(SEMICOLON)
        return node and node or NoOp(line=self.lexer.line)

    def constant_expression(self):
        return self.conditional_expression()

    def expression(self):
        result = list()
        result.append(self.assignment_expression())
        while self.current_token.type == COMMA:
            self.use(COMMA)
            result.append(self.assignment_expression())
        return Expression(
            children=result,
            line=self.lexer.line
        )

    @restorable
    def check_assignment_expression(self):
        if self.current_token.type == ID:
            self.use(ID)
            return self.current_token.type.endswith('ASSIGN')
        return False

    def assignment_expression(self):
        if self.check_assignment_expression():
            node = self.variable()
            while self.current_token.type.endswith('ASSIGN'):
                token = self.current_token
                self.use(token.type)
                return Assign(
                    left=node,
                    op=token,
                    right=self.assignment_expression(),
                    line=self.lexer.line
                )
        return self.conditional_expression()

    def conditional_expression(self):
        node = self.logical_and_expression()
        if self.current_token.type == QUESTION_MARK:
            self.use(QUESTION_MARK)
            texpression = self.expression()
            self.use(COLON)
            fexpression = self.conditional_expression()
            return TernaryOperator(
                condition=node,
                texpression=texpression,
                fexpression=fexpression,
                line=self.lexer.line
            )
        return node

    def logical_and_expression(self):
        node = self.logical_or_expression()
        while self.current_token.type == LOG_AND_OP:
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.logical_or_expression(),
                line=self.lexer.line
            )
        return node

    def logical_or_expression(self):
        node = self.inclusive_or_expression()
        while self.current_token.type == LOG_OR_OP:
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.inclusive_or_expression(),
                line=self.lexer.line
            )
        return node

    def inclusive_or_expression(self):
        node = self.exclusive_or_expression()
        while self.current_token.type == OR_OP:
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.exclusive_or_expression(),
                line=self.lexer.line
            )
        return node

    def exclusive_or_expression(self):
        node = self.and_expression()
        while self.current_token.type == XOR_OP:
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.and_expression(),
                line=self.lexer.line
            )
        return node

    def and_expression(self):
        node = self.equality_expression()
        while self.current_token.type == AND_OP:
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.equality_expression(),
                line=self.lexer.line
            )
        return node

    def equality_expression(self):
        node = self.relational_expression()
        while self.current_token.type in (EQ_OP, NE_OP):
            token = self.current_token
            self.use(token.type)
            return BinaryOperator(
                left=node,
                op=token,
                right=self.relational_expression(),
                line=self.lexer.line
            )
        return node

    def relational_expression(self):
        node = self.shift_expression()
        while self.current_token.type in (LE_OP, LT_OP, GE_OP, GT_OP):
            token = self.current_token
            self.use(token.type)
            return BinaryOperator(
                left=node,
                op=token,
                right=self.shift_expression(),
                line=self.lexer.line
            )
        return node

    def shift_expression(self):
        node = self.additive_expression()
        while self.current_token.type in (LEFT_OP, RIGHT_OP):
            token = self.current_token
            self.use(token.type)
            return BinaryOperator(
                left=node,
                op=token,
                right=self.additive_expression(),
                line=self.lexer.line
            )
        return node

    def additive_expression(self):
        node = self.multiplicative_expression()

        while self.current_token.type in (ADD_OP, SUB_OP):
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.multiplicative_expression(),
                line=self.lexer.line
            )

        return node

    def multiplicative_expression(self):
        node = self.cast_expression()
        while self.current_token.type in (MUL_OP, DIV_OP, MOD_OP):
            token = self.current_token
            self.use(token.type)
            node = BinaryOperator(
                left=node,
                op=token,
                right=self.cast_expression(),
                line=self.lexer.line
            )
        return node

    def parse(self):
        node = self.program()
        if self.current_token.type != EOF:
            self.error("Expected token <EOF> but found <{}>".format(self.current_token.type))

        return node

    @restorable
    def check_cast_expression(self):
        if self.current_token.type == LPAREN:
            self.use(LPAREN)
            if self.current_token.type in [CHAR, DOUBLE, INT, FLOAT]:
                self.use(self.current_token.type)
                return self.current_token.type == RPAREN
        return False

    def cast_expression(self):
        if self.check_cast_expression():
            self.use(LPAREN)
            type_node = self.type_spec()
            self.use(RPAREN)
            return UnaryOperator(
                op=type_node.token,
                expr=self.cast_expression(),
                line=self.lexer.line
            )
        else:
            return self.unary_expression()

    def unary_expression(self):
        if self.current_token.type in (INC_OP, DEC_OP):
            token = self.current_token
            self.use(token.type)
            return UnaryOperator(
                op=token,
                expr=self.unary_expression(),
                line=self.lexer.line
            )
        elif self.current_token.type in (AND_OP, ADD_OP, SUB_OP, LOG_NEG):
            token = self.current_token
            self.use(token.type)
            return UnaryOperator(
                op=token,
                expr=self.cast_expression(),
                line=self.lexer.line
            )
        else:
            return self.postfix_expression()

    def postfix_expression(self):
        node = self.primary_expression()
        if self.current_token.type in (INC_OP, DEC_OP):
            token = self.current_token
            self.use(token.type)
            node = UnaryOperator(
                op=token,
                expr=node,
                line=self.lexer.line,
                prefix=False
            )
        elif self.current_token.type == LPAREN:
            self.use(LPAREN)
            args = list()
            if not self.current_token.type == RPAREN:
                args = self.argument_expression_list()
            self.use(RPAREN)
            if not isinstance(node, Var):
                self.error("Function identifier must be string")
            node = FunctionCall(
                name=node.value,
                args=args,
                line=self.lexer.line
            )
        return node

    def argument_expression_list(self):
        args = [self.assignment_expression()]
        while self.current_token.type == COMMA:
            self.use(COMMA)
            args.append(self.assignment_expression())
        return args

    def primary_expression(self):
        token = self.current_token
        if token.type == LPAREN:
            self.use(LPAREN)
            node = self.expression()
            self.use(RPAREN)
            return node
        elif token.type in (INTEGER_CONST, REAL_CONST, CHAR_CONST):
            return self.constant()
        elif token.type == STRING:
            return self.string()
        else:
            return self.variable()

    def constant(self):
        token = self.current_token
        if token.type == CHAR_CONST:
            self.use(CHAR_CONST)
            return Num(
                token=token,
                line=self.lexer.line
            )
        elif token.type == INTEGER_CONST:
            self.use(INTEGER_CONST)
            return Num(
                token=token,
                line=self.lexer.line
            )
        elif token.type == REAL_CONST:
            self.use(REAL_CONST)
            return Num(
                token=token,
                line=self.lexer.line
            )

    def type_spec(self):
        token = self.current_token
        if token.type in (CHAR, INT, FLOAT, DOUBLE, VOID):
            self.use(token.type)
            return Type(
                token=token,
                line=self.lexer.line
            )

    def variable(self):
        node = Var(
            token=self.current_token,
            line=self.lexer.line
        )
        self.use(ID)
        return node

    def empty(self):
        return NoOp(
            line=self.lexer.line
        )

    def string(self):
        token = self.current_token
        self.use(STRING)
        return String(
            token=token,
            line=self.lexer.line
        )


class SyntaxError(Exception):
    pass
