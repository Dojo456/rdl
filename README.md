# RDL (Regular Definition Language) Parser

A Python-based parser and interpreter for Regular Definition Language (RDL), a language designed for defining Deterministic Finite Automata (DFAs) and Non-deterministic Finite Automata (NFAs). This project implements a lexical analyzer (scanner) and parser to process RDL files and convert automata definitions into a structured JSON representation.

## Features

- Define DFAs and NFAs using a clear, human-readable syntax
- Lexical analysis with support for automata-specific keywords, states, and transitions
- Recursive descent parser for processing RDL syntax
- JSON output format using jsonpickle for machine-readable automata definitions
- Command-line interface for processing RDL files

## Requirements

- Python >= 3.11
- Dependencies:
  - jsonpickle >= 4.0.1
  - pyinstaller >= 6.11.1 (for building executables)

## Installation

1. Clone this repository
2. Create a virtual environment (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install .
   ```

## Usage

Run the parser on an RDL file containing automaton definitions:

```bash
python rdl.py input_file.rdl
```

The program will output a JSON representation of the parsed automaton structure, which can be used for further processing or visualization.

## RDL Syntax

RDL allows you to define finite automata with a clear and concise syntax. The language supports:
- State definitions
- Transition rules
- Start state specification
- Accepting states
- Both deterministic (DFA) and non-deterministic (NFA) automata

Example RDL file for a DFA that accepts the set of all strings over {a, b, c} that contains a number of as that is a multiple of 3:

```
lang global = [a, b, c];

dfa MOD_3(global) {
    start > 1;
    1 >[a] 2 >[a] 3 >[a] 1;
    1 <[b, c];
    2 <[b, c];
    3 <[b, c];
    1 > end;
};
```

## Project Structure

- `rdl.py` - Main entry point
- `scanner.py` - Lexical analyzer/tokenizer implementation
- `parser.py` - Parser implementation for RDL syntax
- `samples/` - Example RDL files demonstrating various DFA definitions
- `pyproject.toml` - Project configuration and dependencies

## Building

To create a standalone executable:

```bash
pyinstaller rdl.py
```

The executable will be created in the `dist` directory.

## Implementation Details

### Scanner (Lexical Analyzer)
The scanner is implemented using a Deterministic Finite Automaton (DFA) that recognizes the following token types:
- Keywords (`dfa`, `lang`, `start`, `end`)
- Identifiers (variable names, symbols within a language)
- Symbols (`{`, `}`, `[`, `]`, `>`, `<`, `,`, `=`, `;`)
- Numbers
- Whitespace

The DFA transitions between states based on the input characters and emits tokens when accepting states are reached. This approach ensures efficient O(n) time complexity for the lexical analysis phase, where n is the input length.

### Parser
The parser implements an LL(1) parsing algorithm using a context-free grammar. Key features include:

- Top-down recursive descent parsing
- Single token lookahead
- Predictive parsing table for efficient decision making

The grammar rules handle:
1. Language definitions
2. Automata declarations (DFA)
3. State transitions
4. Start and accepting state specifications

The LL(1) property ensures that the parser can always decide which production to use by looking at the next token, making the parsing process deterministic and efficient. The implementation uses a symbol stack to traverse depth-first traverse the tree produced by the context free grammar. When a non-terminal is at the top of the stack, the parser performs a lookup in a table that associates each non-terminal to terminal pair with a specific production. The LL(1) property ensures that there is exactly one production per pair.

Example grammar productions:
```
Start -> DefinitionList*
DefinitionList -> Definition
Definition -> LanguageDef
LanguageDef -> 'lang' Identifier '=' '[' SymbolList ']' ';'
AutomatonDef -> ('dfa') Identifier '(' Identifier ')' '{' StateList '}'
// ... additional productions
```

The parser constructs an Abstract Syntax Tree (AST) which is then serialized to JSON using jsonpickle for further processing or visualization.