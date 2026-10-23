import os
from parser import parse

import jsonpickle

from scanner import tokenize


def main():
    import sys

    args = sys.argv[1:]

    if len(args) == 0:
        default = os.getenv("file")

        if not default:
            raise ValueError("Provide an input file")

        input_file = default
    else:
        input_file = args[0]

    with open(input_file, "r") as f:
        data = f.read()

    tokens = tokenize(data)
    parsed = parse(tokens)

    # print(jsonpickle.encode(parsed, indent=2))


if __name__ == "__main__":
    main()
