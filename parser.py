from collections import deque

from scanner import Token, TokenType

# Grammar for the parser
# If non-terminal does not have a production for a token, it is considered an error
grammar: dict[
    str,
    dict[Token | TokenType, tuple[Token | str | TokenType | None, ...]],
] = {
    "start": {
        TokenType.KEYWORD: ("declaration-list",),
    },
    "declaration-list": {
        TokenType.KEYWORD: ("declaration", "declaration-list"),
        TokenType.END: (None,),
    },
    "declaration": {
        Token(type=TokenType.KEYWORD, value="dfa"): (
            Token(type=TokenType.KEYWORD, value="dfa"),
            "dfa-declaration",
            Token(type=TokenType.SEMICOLON, value=";"),
        ),
        Token(type=TokenType.KEYWORD, value="lang"): (
            Token(type=TokenType.KEYWORD, value="lang"),
            "lang-declaration",
            Token(type=TokenType.SEMICOLON, value=";"),
        ),
        TokenType.END: (None,),
    },
    "dfa-declaration": {
        TokenType.IDENTIFIER: (
            TokenType.IDENTIFIER,
            Token(type=TokenType.SYMBOL, value="("),
            "dfa-language-specifier",
            Token(type=TokenType.SYMBOL, value=")"),
            Token(type=TokenType.SYMBOL, value="{"),
            "dfa-body",
            Token(type=TokenType.SYMBOL, value="}"),
        ),
    },
    "dfa-language-specifier": {
        Token(type=TokenType.SYMBOL, value="["): ("symbol-group",),
        TokenType.IDENTIFIER: (TokenType.IDENTIFIER,),
    },
    "lang-declaration": {
        TokenType.IDENTIFIER: (
            TokenType.IDENTIFIER,
            Token(type=TokenType.SYMBOL, value="="),
            "symbol-group",
        ),
    },
    "dfa-body": {
        TokenType.KEYWORD: ("dfa-transition",),
        TokenType.IDENTIFIER: ("dfa-transition",),
    },
    "dfa-transition": {
        TokenType.NUMBER: (TokenType.NUMBER, "transition-direction"),
        Token(type=TokenType.KEYWORD, value="start"): (
            Token(type=TokenType.KEYWORD, value="start"),
            Token(type=TokenType.SYMBOL, value=">"),
            "transition-to",
        ),
        Token(type=TokenType.KEYWORD, value="end"): (None,),
        Token(type=TokenType.SYMBOL, value="}"): (None,),
    },
    "transition-direction": {
        Token(type=TokenType.SYMBOL, value=">"): ("transition-limits", "transition-to"),
        Token(type=TokenType.SYMBOL, value="<"): ("transition-limits",),
        TokenType.NUMBER: ("transition-limits",),
    },
    "transition-to": {
        TokenType.NUMBER: (TokenType.NUMBER, "linked-transition"),
        Token(type=TokenType.KEYWORD, value="end"): (
            Token(type=TokenType.KEYWORD, value="end"),
        ),
    },
    "linked-transition": {
        TokenType.NUMBER: ("dfa-transition",),
        Token(type=TokenType.SYMBOL, value="}"): (None,),
        Token(type=TokenType.SEMICOLON, value=";"): (None,),
    },
    "transition-limits": {
        Token(type=TokenType.SYMBOL, value="["): ("symbol-group",),
        Token(type=TokenType.SYMBOL, value="}"): (None,),
        TokenType.IDENTIFIER: (None,),
        TokenType.NUMBER: (None,),
        TokenType.END: (None,),
    },
    "symbol-group": {
        Token(type=TokenType.SYMBOL, value="["): (
            Token(type=TokenType.SYMBOL, value="["),
            "symbol-list",
            Token(type=TokenType.SYMBOL, value="]"),
        ),
    },
    "symbol-list": {
        TokenType.IDENTIFIER: (TokenType.IDENTIFIER, "symbol-list-separator"),
    },
    "symbol-list-separator": {
        Token(type=TokenType.SYMBOL, value=","): (
            Token(type=TokenType.SYMBOL, value=","),
            "symbol-list",
        ),
        Token(type=TokenType.SYMBOL, value="]"): (None,),
    },
}


def matches(token: Token, rule: Token | TokenType) -> bool:
    if isinstance(rule, Token):
        return token == rule
    elif isinstance(rule, TokenType):
        return token.type == rule


class ParseTokenMismatchError(ValueError):
    def __init__(
        self, expected: Token | TokenType, found: Token | TokenType, *args: object
    ) -> None:
        self.expected = expected
        self.found = found

        super().__init__(*args)

    def __str__(self) -> str:
        return f"Expected {str(self.expected)}, found {str(self.found)}"


def parse(tokens: list[Token]):
    stack: deque[tuple[Token | str | TokenType | None, list[str | Token]]] = deque(
        [("start", [])]
    )

    initial_tokens_length = len(tokens)
    token_stack = deque(tokens)

    parse_tree = {}

    def node_at(path: list[str | Token]) -> dict:
        """Navigates to the node from the parse_tree that is at the given path. Returns the object reference, meaning is editable and has all nested children."""
        node = parse_tree
        for key in path:
            next = node[key]
            if next is None:
                next = {}
                node[key] = next
            node = next
        return node

    top_entry = None

    try:
        while token_stack:
            token = token_stack[0]

            # Whitespace tokens are ignored, simply pop left and remove it
            if token.type == TokenType.WHITESPACE:
                token_stack.popleft()
                continue

            # Pop the top of the stack and get the current node within the output AST
            top_entry = stack.pop()
            top = top_entry[0]
            node_path = top_entry[1]
            current_node = node_at(node_path)

            # If the top of the stack is a non-terminal, we need to find a production that matches the token
            if isinstance(top, str):
                grammar_rule = grammar[top]

                found_match = False

                for match, production in grammar_rule.items():
                    if matches(token, match):
                        stack.extend(
                            [
                                (production_item, node_path + [top])
                                for production_item in reversed(production)
                            ]
                        )
                        found_match = True

                        break

                new_node = {"token_index": initial_tokens_length - len(token_stack)}
                current_node[top] = new_node

                if not found_match:
                    raise ValueError(f"No production found for {token}")

            # If the top of the stack is a token type, check if it matches the current token type and push token
            elif isinstance(top, TokenType):
                if top == token.type:
                    token_stack.popleft()

                    # If terminal, add it to the parse tree
                    current_node[token] = None
                else:
                    raise ParseTokenMismatchError(top, token.type)
            # If the top of the stack is a token, check if it matches the current token and push token
            elif isinstance(top, Token):
                if top == token:
                    token_stack.popleft()

                    # If terminal, add it to the parse tree
                    current_node[token] = None
                else:
                    raise ParseTokenMismatchError(top, token)
            # Epsilon production
            elif top is None:
                continue

    except Exception as e:
        print(e.__class__, "\n")

        if top_entry:  # Attempt to recreate source code from symbol trace and print it
            path = top_entry[1]

            node = node_at(path)

            # Current node's token index
            n_ti = node.get("token_index")

            # Traverse up (parent) node's token index
            tu_ti = n_ti

            if n_ti:
                for i in range(len(path)):
                    traverse_up = node_at(path[: -1 * i])

                    tu_ti_temp = traverse_up.get("token_index")

                    if tu_ti_temp and tu_ti_temp != n_ti:
                        tu_ti = tu_ti_temp

                # Print all children
                s = deque([node])

                while len(s) > 0:
                    n = s.popleft()

                    if not isinstance(n, dict):
                        continue

                    n_ti_temp = n.get("token_index")

                    if n_ti_temp and n_ti_temp > n_ti:
                        n_ti = n_ti_temp

                    for c in n.values():
                        s.appendleft(c)

                print("".join([t.value for t in tokens[tu_ti : n_ti + 1]]))

        print(e)

    return parse_tree
