from enum import Enum
import re
from typing import TypedDict


def main():
    import sys

    args = sys.argv[1:]

    if len(args) == 0:
        raise ValueError("Provide an input file")
    else:
        input_file = args[0]

    with open(input_file, "r") as f:
        data = f.read()

    print(data)


class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    DEFINITION = "DEFINITION"
    STATE = "STATE"
    STRING = "STRING"
    SYMBOL = "SYMBOL"
    WHITESPACE = "WHITESPACE"


class Token(TypedDict):
    type: TokenType
    value: str


def tokenize(data: str):
    class State(Enum):
        prase

        END = "END"

    tokens: list[Token] = []

    current_token: Token = Token(type=TokenType.WHITESPACE, value="")

    def yield_token(token_type: TokenType):
        nonlocal current_token

        current_token.type = token_type
        tokens.append(current_token)
        current_token = Token(type=TokenType.WHITESPACE, value="")

    def add_to_current_token(char: str):
        nonlocal current_token

        current_token.value += char

    state: State = State.PARSE_DFA_KEYWORD

    i = 0

    while i < len(data):
        char = data[i]

        match state:
            case State.PARSE_DFA_KEYWORD_ONE:
                if char == "d" or char == "D":
                    state = State.PARSE_DFA_KEYWORD_TWO
                    add_to_current_token(char)
                else:
                    raise ValueError(f"Expected 'd' in DFA keyword, got {char}")
            case State.PARSE_DFA_KEYWORD_TWO:
                if char == "f" or char == "F":
                    state = State.PARSE_DFA_KEYWORD_THREE
                    add_to_current_token(char)
                else:
                    raise ValueError(f"Expected 'f' in DFA keyword, got {char}")
            case State.PARSE_DFA_KEYWORD_THREE:
                if char == "a" or char == "A":
                    yield_token(TokenType.DFA_KEYWORD)
                    state = State.FIND_START_DFA_IDENTIFIER
                else:
                    raise ValueError(f"Expected 'a' in DFA keyword, got {char}")
            case State.FIND_START_DFA_IDENTIFIER:
                if char == " ":
                    add_to_current_token(char)
                elif re.match(r"[a-zA-Z0-9_-]", char):
                    yield_token(TokenType.WHITESPACE)
                    add_to_current_token(char)
                    state = State.PARSE_DFA_IDENTIFIER
                else:
                    raise ValueError(f"Expected an identifier, got {char}")
            case State.PARSE_DFA_IDENTIFIER:
                if re.match(r"[a-zA-Z0-9_-]", char):
                    add_to_current_token(char)
                elif char == " ":
                    yield_token(TokenType.DFA_IDENTIFIER)
                    state = State.FIND_START_SYMBOL_PATTERN
                else:
                    raise ValueError(f"Expected an identifier, got {char}")
            case State.FIND_START_SYMBOL_PATTERN:
                if char == " ":
                    add_to_current_token(char)
                elif char == "[":
                    yield_token(TokenType.WHITESPACE)
                    add_to_current_token(char)
                    yield_token(TokenType.START_SYMBOL_PATTERN)
                    state = State.PARSE_SYMBOL_PATTERN
                else:
                    raise ValueError(f"Expected start of symbol pattern, got {char}")
            case State.PARSE_SYMBOL_PATTERN:
                if re.match(r"[a-zA-Z]", char):
                    add_to_current_token(char)
                elif char == ",":
                    yield_token(TokenType.SYMBOL)
                    state = State.PARSE_SYMBOL_PATTERN_SEPARATOR
                else:
                    raise ValueError(f"Expected a symbol, got {char}")
            case State.PARSE_SYMBOL_PATTERN_SEPARATOR:
                if char == ",":
                    add_to_current_token(char)
                    yield_token(TokenType.SYMBOL_PATTERN_SEPARATOR)
                else:
                    raise ValueError(f"Expected ',' in symbol pattern, got {char}")
            case State.PARSE_END_SYMBOL_PATTERN:
                if char == "]":
                    add_to_current_token(char)
                    yield_token(TokenType.END_SYMBOL_PATTERN)
            case State.FIND_START_DFA_DEFINITION:
                if char == "{":
                    add_to_current_token(char)
                    yield_token(TokenType.START_DFA_DEFINITION)
                else:
                    raise ValueError(f"Expected '{"{"}' in DFA definition, got {char}")
            case State.PARSE_STATE:
                if re.match(r"[a-zA-Z0-9_-]", char):
                    add_to_current_token(char)
                elif char == " ":
                    yield_token(TokenType.STATE)
                else:
                    raise ValueError(f"Expected a state, got {char}")

        i += 1


if __name__ == "__main__":
    main()
