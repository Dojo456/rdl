from scanner import tokenize
from parser import parse
import jsonpickle


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
    parsed = parse(tokens)

    print(jsonpickle.encode(parsed, indent=2))


if __name__ == "__main__":
    main()
