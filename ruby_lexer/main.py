import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lexer import Lexer, TokenType


def print_table(tokens):
    print(f"{'LINE':<6}{'COL':<6}{'TYPE':<14}VALUE")
    print('-' * 46)
    for tok in tokens:
        print(f"{tok.line:<6}{tok.col:<6}{tok.type.name:<14}{tok.value}")


def main():
    parser = argparse.ArgumentParser(description='Ruby Lexer — tokenize Ruby source code')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('file', nargs='?', metavar='FILE', help='Ruby source file to tokenize')
    group.add_argument('-e', metavar='CODE', dest='inline', help='Tokenize an inline Ruby code string')
    args = parser.parse_args()

    if args.inline is not None:
        source = args.inline
    else:
        path = Path(args.file)
        if not path.exists():
            print(f"Error: file '{args.file}' not found", file=sys.stderr)
            sys.exit(1)
        source = path.read_text(encoding='utf-8')

    tokens = Lexer(source).tokenize()
    print_table(tokens)


if __name__ == '__main__':
    main()
