from enum import Enum
import re
from typing import NamedTuple, TypedDict


def main():
    import sys

    args = sys.argv[1:]

    if len(args) == 0:
        raise ValueError("Provide an input file")
    else:
        input_file = args[0]

    with open(input_file, "r") as f:
        data = f.read()

    tokens = tokenize(data)

    print(tokens)


class TokenType(Enum):
    KEYWORD = "KEYWORD"
    IDENTIFIER = "IDENTIFIER"
    NUMBER = "NUMBER"
    SYMBOL = "SYMBOL"
    WHITESPACE = "WHITESPACE"
    SEMICOLON = "SEMICOLON"
    END = "END"

    def __repr__(self):
        return self.value


class Token(NamedTuple):
    type: TokenType
    value: str

    def __repr__(self):
        return f"Token(type={self.type}, value={self.value})"


keyword_tokens = frozenset(["dfa", "start", "end", "lang", "sublang", "state"])


def tokenize(data: str) -> list[Token]:
    tokens: list[Token] = []

    whitespace = re.compile(r"[ \t\n\r]")
    semicolon = re.compile(r";")
    identifier = re.compile(r"[a-zA-Z\-\_]")
    number = re.compile(r"[0-9]")
    symbol = re.compile(r"[\[\]\{\}<\>\,\=\(\)]")

    language = [whitespace, identifier, number, symbol, semicolon]

    transition_table: list[list[int | None]] = [
        # Input character
        # whitespace, letter, number, symbol, semicolon
        [5, 1, 3, 6, 9],  # 0 start state
        [2, 1, 1, 2, 2],  # 1 first letter of identifier or keyword
        [None, None, None, None, None],  # 2 yield identifier or keyword
        [4, -1, 3, -1, 4],  # 3 first letter of number
        [None, None, None, None, None],  # 4 yield number
        [7, 7, 7, 7, 8],  # 5 first letter of whitespace
        [8, 8, 8, 8, 8],  # 6 first letter of symbol
        [None, None, None, None, None],  # 7 yield whitespace
        [None, None, None, None, None],  # 8 yield symbol
        [10, 10, 10, 10, 10],  # 9 first letter of semicolon
        [None, None, None, None, None],  # 10 yield semicolon
    ]

    end_state_types = {
        2: lambda x: TokenType.KEYWORD if x in keyword_tokens else TokenType.IDENTIFIER,
        4: lambda _: TokenType.NUMBER,
        7: lambda _: TokenType.WHITESPACE,
        8: lambda _: TokenType.SYMBOL,
        10: lambda _: TokenType.SEMICOLON,
    }

    state: int = 0
    current_token = ""

    i = 0

    while i < len(data):
        char = data[i]
        next_state: int | None = -1

        for j, language_regex in enumerate(language):
            if language_regex.match(char):
                next_state = transition_table[state][j]

        if next_state == -1:
            raise ValueError(f"Unexpected character: {char}")

        # at end state, yield token
        if next_state is None:
            i -= 1
            current_token = current_token[:-1]

            tokens.append(
                Token(type=end_state_types[state](current_token), value=current_token)
            )
            current_token = ""
            state = 0
            continue

        current_token += char
        i += 1
        state = next_state

    return tokens + [Token(type=TokenType.END, value="")]


if __name__ == "__main__":
    main()
