from collections import deque

import jsonpickle

from scanner import Token, TokenType

# Grammar for the parser
# If non-terminal does not have a production for a token, it is considered an error
# Syntax is as follows for each grammar rule:
# Given current state, match from a list of rules given the next token (LL1)
# On match, the rule should yield a list of states to be yielded
# If is a terminal, should yield (None,) as cannot yield tuples of length 1 for Python syntax reasons. Technically you can, but just more annoying to write you have to do something like tuple([None])
grammar: dict[
    str,
    dict[Token | TokenType, tuple[Token | str | TokenType | None, ...]],
] = {
    "start": {
        TokenType.KEYWORD: ("declaration-list", TokenType.END),
    },
    "declaration-list": {
        TokenType.KEYWORD: ("declaration", "declaration-list"),
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
        TokenType.NUMBER: ("transition-list",),
        TokenType.KEYWORD: ("transition-list",),
        Token(type=TokenType.SYMBOL, value="}"): (None,),
    },
    "transition-list": {
        TokenType.NUMBER: ("dfa-transition", "transition-list"),
        TokenType.KEYWORD: (
            "dfa-transition",
            "transition-list",
        ),
        Token(type=TokenType.SYMBOL, value="}"): (None,),
    },
    "dfa-transition": {
        TokenType.NUMBER: (TokenType.NUMBER, "transition-direction", "transition-to"),
        Token(type=TokenType.KEYWORD, value="start"): (
            Token(type=TokenType.KEYWORD, value="start"),
            "transition-direction-forward",
            "transition-to",
        ),
    },
    "transition-direction-forward": {
        Token(type=TokenType.SYMBOL, value=">"): (
            Token(type=TokenType.SYMBOL, value=">"),
            "transition-limits",
        ),
    },
    "transition-direction": {
        Token(type=TokenType.SYMBOL, value=">"): (
            Token(type=TokenType.SYMBOL, value=">"),
            "transition-limits",
        ),
        Token(type=TokenType.SYMBOL, value="<"): (
            Token(type=TokenType.SYMBOL, value="<"),
            "transition-limits",
        ),
    },
    "transition-to": {
        TokenType.NUMBER: (TokenType.NUMBER, "linked-transition"),
        Token(type=TokenType.KEYWORD, value="end"): (
            Token(type=TokenType.KEYWORD, value="end"),
            "linked-transition",
        ),
    },
    "linked-transition": {
        TokenType.NUMBER: ("transition-direction",),
        Token(type=TokenType.SEMICOLON, value=";"): (
            Token(type=TokenType.SEMICOLON, value=";"),
        ),
    },
    "transition-limits": {
        Token(type=TokenType.SYMBOL, value="["): ("symbol-group",),
        TokenType.NUMBER: (None,),
        Token(type=TokenType.KEYWORD, value="end"): (None,),
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
        self,
        expected: Token | TokenType,
        found: Token | TokenType,
        *messages: str,
        **kwargs: dict,
    ) -> None:
        self.expected = expected
        self.found = found
        self.messages = messages

        super().__init__(**kwargs)

    def __str__(self) -> str:
        return f"Expected {str(self.expected)}, found {str(self.found)}.\n" + "\n".join(
            self.messages
        )


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

    def print_source_code_around_node(path: list[str | Token]):
        node = node_at(path)

        # Current node's token index
        n_ti = node.get("token_index")

        # Traverse up (parent) node's token index
        tu_ti = n_ti

        if n_ti:
            for i in range(len(path)):
                traverse_up = node_at(path[: -1 * (i + 1)])

                tu_ti_temp = traverse_up.get("token_index")

                if tu_ti_temp and tu_ti_temp != n_ti:
                    tu_ti = tu_ti_temp
                    break

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

            print("".join([t.value for t in tokens[tu_ti : n_ti + 1]]), "\n")

    # def print_source_code_around_node_line(path: list[str | Token]):
    #     node = node_at(path)

    #     # Current node's token index
    #     node_ti = node.get("token_index")

    #     if node_ti:
    #         start_ti = node_ti

    #         start_lines = 0

    #         for i in range(node_ti):
    #             if start_lines >= 3:
    #                 break

    #             c = node_at(path[: -1 * (1 + i)])

    #             if isinstance(c, Token):
    #                 start_lines += c.value.count("\n")
    #             elif is

    #             current_ti = node.get("token_index")

    #             if current_ti and current_ti < node_ti:
    #                 start_ti = current_ti

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
                    raise ValueError(
                        f"No production found for {token}. Current 'top' is {top} with grammar rules:\n{jsonpickle.encode(grammar_rule, indent=2, unpicklable=False)}"
                    )

            # If the top of the stack is a token type, check if it matches the current token type and push token
            elif isinstance(top, TokenType):
                if top == token.type:
                    token_stack.popleft()

                    # If terminal, add it to the parse tree
                    current_node[token] = None
                else:
                    raise ParseTokenMismatchError(
                        top,
                        token.type,
                        f"Current 'top' is {top}",
                    )
            # If the top of the stack is a token, check if it matches the current token and push token
            elif isinstance(top, Token):
                if top == token:
                    token_stack.popleft()

                    # If terminal, add it to the parse tree
                    current_node[token] = None
                else:
                    raise ParseTokenMismatchError(
                        top,
                        token,
                        f"Current 'top' is {top}",
                    )
            # Epsilon production
            elif top is None:
                continue

    except Exception as e:
        print(e.__class__, "\n")

        if top_entry:  # Attempt to recreate source code from symbol trace and print it
            path = top_entry[1]

            print_source_code_around_node(path)

        print(e)

    return parse_tree
