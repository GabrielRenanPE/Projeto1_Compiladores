# Projeto1_Compiladores
# ⚙️ Compilador de Subconjunto Pascal em Python

Este projeto é a implementação do *front-end* de um compilador para um subconjunto da linguagem Pascal, desenvolvido do zero em Python. Ele é capaz de ler um código-fonte, validar suas regras léxicas e sintáticas, gerenciar o escopo de variáveis e gerar uma Árvore Sintática Abstrata (AST).

---

## 🏗️ Arquitetura do Projeto

O compilador foi construído de forma modular e didática, dividido em quatro pilares principais:

1. **Analisador Léxico (Lexer):** Varre o código-fonte caractere por caractere e, utilizando Expressões Regulares (Regex), converte o texto bruto em uma sequência lógica de `Tokens` (palavras-chave, operadores, identificadores, etc.), ignorando espaços em branco e comentários.
2. **Tabela de Símbolos:** Atua como a memória do compilador. Utiliza uma estrutura de Pilha de Ambientes (lista de dicionários) para garantir que as variáveis respeitem regras de escopo global e local (dentro de *procedures*).
3. **Analisador Sintático (Parser):** Utiliza a técnica de *Descida Recursiva* para validar se a sequência de Tokens forma frases válidas segundo a gramática da linguagem.
4. **Gerador de AST (Árvore Sintática Abstrata):** À medida que o Parser valida a sintaxe, ele empacota as operações em "Nós" lógicos, gerando uma estrutura de dados em formato de árvore que representa o comportamento do programa de forma hierárquica.

---

## 🚀 Como Executar (Passo a Passo)

O projeto foi construído utilizando apenas as bibliotecas nativas do Python, o que significa que não é necessário instalar dependências externas (como bibliotecas via `pip`).

### 1. Pré-requisitos
* Ter o **Python 3.x** instalado em sua máquina.

### 2. Executando o código
1. Salve o código fonte do compilador em um arquivo chamado, por exemplo, `compilador.py`.
2. Abra o terminal do seu sistema operacional (ou terminal integrado da sua IDE, como o VS Code).
3. Navegue até a pasta onde o arquivo foi salvo.
4. Execute o seguinte comando:
   ```bash
   python compilador.py
