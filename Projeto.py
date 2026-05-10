import re

# EXCEÇÕES

class ErroLexico(Exception): pass
class ErroSintatico(Exception): pass
class ErroSemantico(Exception): pass


# LEXER

class Token:
    def __init__(self, tipo, valor, linha):
        self.tipo = tipo
        self.valor = valor
        self.linha = linha

    def __repr__(self):
        return f"Token({self.tipo}, '{self.valor}', linha {self.linha})"

class Lexer:
    def __init__(self, codigo):
        self.codigo = codigo
        self.lista_de_tokens = []
        self.posicao_atual = 0
        self._varrer_codigo()

    def _varrer_codigo(self):
        regras = [
            ('COMMENT',    r'\{.*?\}'),
            ('WHITESPACE', r'\s+'),
            ('ASSIGN',     r':='),
            ('RELOP',      r'<=|>=|<>|<|>|='),
            ('ADDOP',      r'\+|-|\bOR\b'),
            ('MULOP',      r'\*|/|\bDIV\b|\bMOD\b|\bAND\b'),
            ('KEYWORD',    r'\b(?:program|var|procedure|begin|end|if|then|else|while|do|integer|real|not)\b'),
            ('NUM',        r'\d+(?:\.\d+)?(?:[eE][+-]?\d+)?'),
            ('ID',         r'[a-zA-Z][a-zA-Z0-9]*'),
            ('SEMI',       r';'),
            ('COLON',      r':'),
            ('COMMA',      r','),
            ('DOT',        r'\.'),
            ('LPAREN',     r'\('),
            ('RPAREN',     r'\)'),
        ]

        partes = [f"(?P<{nome}>{padrao})" for nome, padrao in regras]
        regex_gigante = re.compile("|".join(partes), re.DOTALL | re.IGNORECASE)

        numero_da_linha = 1
        for match in regex_gigante.finditer(self.codigo):
            tipo = match.lastgroup
            valor = match.group(tipo)

            if tipo in ('WHITESPACE', 'COMMENT'):
                numero_da_linha += valor.count('\n')
                continue

            if tipo == 'KEYWORD':
                valor = valor.lower()

            self.lista_de_tokens.append(Token(tipo, valor, numero_da_linha))

    def proximo_token(self):
        if self.posicao_atual < len(self.lista_de_tokens):
            token = self.lista_de_tokens[self.posicao_atual]
            self.posicao_atual += 1
            return token
        return Token('EOF', '', -1)

# TABELA DE SÍMBOLOS

class TabelaDeSimbolos:
    def __init__(self):
        self.escopos = [{}]

    def entrar_escopo(self):
        self.escopos.append({})

    def sair_escopo(self):
        if len(self.escopos) > 1:
            self.escopos.pop()

    def declarar(self, nome, tipo):
        escopo_atual = self.escopos[-1]
        if nome in escopo_atual:
            raise ErroSemantico(f"A variável '{nome}' já foi declarada neste escopo!")
        escopo_atual[nome] = tipo

    def buscar(self, nome):
        for escopo in reversed(self.escopos):
            if nome in escopo:
                return escopo[nome]
        return None

 
# AST (NÓ)

class No:
    def __init__(self, tipo, **dados):
        self.tipo = tipo
        for chave, valor in dados.items():
            setattr(self, chave, valor)

    def __repr__(self):
        return f"No({self.tipo})"


# PARSER

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer
        self.token_atual = self.lexer.proximo_token()
        self.tabela = TabelaDeSimbolos()

    def erro(self, esperado):
        raise ErroSintatico(
            f"Linha {self.token_atual.linha}: Esperava '{esperado}' "
            f"mas encontrou '{self.token_atual.valor}' ({self.token_atual.tipo})"
        )

    def consumir(self, tipo_ou_valor):
        if self.token_atual.tipo == tipo_ou_valor or self.token_atual.valor == tipo_ou_valor:
            token_consumido = self.token_atual
            self.token_atual = self.lexer.proximo_token()
            return token_consumido
        else:
            self.erro(tipo_ou_valor)

    def analisar(self):
        arvore = self.programa()
        if self.token_atual.tipo != 'EOF':
            raise ErroSintatico("Tem código sobrando após o ponto final do programa!")
        return arvore

    def programa(self):
        self.consumir('program')
        nome_programa = self.token_atual.valor
        self.consumir('ID')
        self.consumir('SEMI')

        declaracoes = self.declaracoes()
        comandos = self.bloco()
        self.consumir('DOT')

        return No('programa', nome=nome_programa, declaracoes=declaracoes, comandos=comandos)

    def declaracoes(self):
        decls = []
        if self.token_atual.valor == 'var':
            self.consumir('var')
            decls.extend(self.declaracoes_de_variaveis())

        decls.extend(self.declaracoes_de_procedures())
        return decls

    def declaracoes_de_variaveis(self):
        vars_declaradas = []
        vars_declaradas.extend(self.uma_declaracao_de_variavel())

        while self.token_atual.tipo == 'ID':
            vars_declaradas.extend(self.uma_declaracao_de_variavel())

        return vars_declaradas

    def uma_declaracao_de_variavel(self):
        nomes = self.lista_de_identificadores()
        self.consumir('COLON')
        tipo_da_var = self.tipo()
        self.consumir('SEMI')

        nos = []
        for nome in nomes:
            self.tabela.declarar(nome, tipo_da_var)
            nos.append(No('var_decl', nome=nome, tipo_var=tipo_da_var))

        return nos

    def lista_de_identificadores(self):
        lista = [self.token_atual.valor]
        self.consumir('ID')
        while self.token_atual.tipo == 'COMMA':
            self.consumir('COMMA')
            lista.append(self.token_atual.valor)
            self.consumir('ID')
        return lista

    def tipo(self):
        if self.token_atual.valor in ['integer', 'real']:
            tipo = self.token_atual.valor
            self.consumir('KEYWORD')
            return tipo
        self.erro("integer ou real")

    def declaracoes_de_procedures(self):
        procs = []
        while self.token_atual.valor == 'procedure':
            self.consumir('procedure')
            nome_proc = self.token_atual.valor
            self.tabela.declarar(nome_proc, 'procedure')
            self.consumir('ID')
            self.consumir('SEMI')

            self.tabela.entrar_escopo()
            decls_locais = self.declaracoes()
            corpo = self.bloco()
            self.consumir('SEMI')
            self.tabela.sair_escopo()

            procs.append(No('procedure_decl', nome=nome_proc, declaracoes=decls_locais, comandos=corpo))

        return procs

    def bloco(self):
        self.consumir('begin')
        comandos = self.lista_de_comandos()
        self.consumir('end')
        return comandos

    def lista_de_comandos(self):
        comandos = [self.comando()]
        while self.token_atual.tipo == 'SEMI':
            self.consumir('SEMI')
            comandos.append(self.comando())
        return comandos

    def comando(self):
        if self.token_atual.tipo == 'ID':
            nome_var = self.token_atual.valor
            token_id = self.token_atual
            self.consumir('ID')

            if self.tabela.buscar(nome_var) is None:
                raise ErroSemantico(f"'{nome_var}' não foi declarado! Linha {token_id.linha}")

            if self.token_atual.tipo == 'ASSIGN':
                self.consumir('ASSIGN')
                return No('atribuicao', variavel=nome_var, expressao=self.expressao())

            elif self.token_atual.tipo == 'LPAREN':
                self.consumir('LPAREN')
                self.consumir('RPAREN')
                return No('chamada_procedure', nome=nome_var)

        elif self.token_atual.valor == 'begin':
            return No('bloco', comandos=self.bloco())

        elif self.token_atual.valor == 'if':
            self.consumir('if')
            condicao = self.expressao()
            self.consumir('then')
            cmd_then = self.comando()

            cmd_else = No('noop')
            if self.token_atual.valor == 'else':
                self.consumir('else')
                cmd_else = self.comando()

            return No('if', condicao=condicao, cmd_then=cmd_then, cmd_else=cmd_else)

        elif self.token_atual.valor == 'while':
            self.consumir('while')
            condicao = self.expressao()
            self.consumir('do')
            return No('while', condicao=condicao, comando=self.comando())

        return No('noop')

    def expressao(self):
        no = self.expressao_simples()
        if self.token_atual.tipo == 'RELOP':
            operador = self.token_atual.valor
            self.consumir('RELOP')
            no = No('op_binaria', esquerda=no, operador=operador, direita=self.expressao_simples())
        return no

    def expressao_simples(self):
        op_unario = None
        if self.token_atual.tipo == 'ADDOP':
            op_unario = self.token_atual.valor
            self.consumir('ADDOP')

        no = self.termo()

        if op_unario:
            no = No('op_unaria', operador=op_unario, fator=no)

        while self.token_atual.tipo == 'ADDOP':
            operador = self.token_atual.valor
            self.consumir('ADDOP')
            no = No('op_binaria', esquerda=no, operador=operador, direita=self.termo())

        return no

    def termo(self):
        no = self.fator()
        while self.token_atual.tipo == 'MULOP':
            operador = self.token_atual.valor
            self.consumir('MULOP')
            no = No('op_binaria', esquerda=no, operador=operador, direita=self.fator())
        return no

    def fator(self):
        token = self.token_atual

        if token.tipo == 'ID':
            if self.tabela.buscar(token.valor) is None:
                raise ErroSemantico(f"Variável '{token.valor}' não declarada. Linha {token.linha}")
            self.consumir('ID')
            return No('variavel', nome=token.valor)

        elif token.tipo == 'NUM':
            self.consumir('NUM')
            return No('numero', valor=token.valor)

        elif token.tipo == 'LPAREN':
            self.consumir('LPAREN')
            no = self.expressao()
            self.consumir('RPAREN')
            return no

        elif token.valor == 'not':
            self.consumir('KEYWORD')
            return No('op_unaria', operador='not', fator=self.fator())

        else:
            self.erro("uma variável, número, '(' ou not")

# FUNÇÃO PARA IMPRIMIR AST

def imprimir_ast(no, nivel=0):
    recuo = "  " * nivel

    if no is None or no.tipo == 'noop':
        return

    if no.tipo == 'programa':
        print(f"{recuo}Programa: {no.nome}")
        for decl in no.declaracoes:
            imprimir_ast(decl, nivel + 1)
        for cmd in no.comandos:
            imprimir_ast(cmd, nivel + 1)

    elif no.tipo == 'var_decl':
        print(f"{recuo}Variável declarada: {no.nome} ({no.tipo_var if hasattr(no, 'tipo_var') else no.tipo})")

    elif no.tipo == 'procedure_decl':
        print(f"{recuo}Procedure: {no.nome}")
        for decl in no.declaracoes:
            imprimir_ast(decl, nivel + 1)
        for cmd in no.comandos:
            imprimir_ast(cmd, nivel + 1)

    elif no.tipo == 'bloco':
        for cmd in no.comandos:
            imprimir_ast(cmd, nivel)

    elif no.tipo == 'atribuicao':
        print(f"{recuo}Atribuição: {no.variavel} :=")
        imprimir_ast(no.expressao, nivel + 1)

    elif no.tipo == 'chamada_procedure':
        print(f"{recuo}Chamada: {no.nome}()")

    elif no.tipo == 'if':
        print(f"{recuo}Se (if):")
        imprimir_ast(no.condicao, nivel + 1)
        print(f"{recuo}Então (then):")
        imprimir_ast(no.cmd_then, nivel + 1)
        if no.cmd_else.tipo != 'noop':
            print(f"{recuo}Senão (else):")
            imprimir_ast(no.cmd_else, nivel + 1)

    elif no.tipo == 'while':
        print(f"{recuo}Enquanto (while):")
        imprimir_ast(no.condicao, nivel + 1)
        print(f"{recuo}Faça (do):")
        imprimir_ast(no.comando, nivel + 1)

    elif no.tipo == 'op_binaria':
        print(f"{recuo}Operação: {no.operador}")
        imprimir_ast(no.esquerda, nivel + 1)
        imprimir_ast(no.direita, nivel + 1)

    elif no.tipo == 'op_unaria':
        print(f"{recuo}Op. Unária: {no.operador}")
        imprimir_ast(no.fator, nivel + 1)

    elif no.tipo == 'numero':
        print(f"{recuo}Número: {no.valor}")

    elif no.tipo == 'variavel':
        print(f"{recuo}Variável: {no.nome}")


# EXECUÇÃO

codigo_pascal = """
program exemplo;

var
  x, y : integer;
  z : real;

procedure teste;
var
  a : integer;
begin
  a := 10;
  if a > 5 then
    x := a
  else
    x := 0
end;

begin
  x := 1;
  y := 2;
  z := 3.5;

  teste();

  while x < y do
  begin
    x := x + 1
  end
end.
"""

if __name__ == "__main__":
    print("Iniciando compilação e geração da AST...\n")
    meu_lexer = Lexer(codigo_pascal)
    meu_parser = Parser(meu_lexer)

    try:
        arvore = meu_parser.analisar()
        print("✅ Sintaxe correta! Árvore Gerada:\n")
        imprimir_ast(arvore)
    except Exception as erro:
        print(f"❌ {erro}")
