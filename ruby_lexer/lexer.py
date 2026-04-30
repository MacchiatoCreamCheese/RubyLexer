import re
from enum import Enum, auto
from dataclasses import dataclass
from typing import List


class TokenType(Enum):
    KEYWORD      = auto()
    IDENTIFIER   = auto()
    CONSTANT     = auto()
    INSTANCE_VAR = auto()
    CLASS_VAR    = auto()
    GLOBAL_VAR   = auto()
    UNKNOWN      = auto()
    EOF          = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int
    col: int


KEYWORDS: frozenset = frozenset({
    "def", "class", "end", "if", "else", "elsif", "unless",
    "while", "until", "for", "in", "do", "return", "yield",
    "begin", "rescue", "ensure", "raise", "true", "false",
    "nil", "self", "super", "and", "or", "not", "then",
    "case", "when", "module", "next", "break", "retry",
    "redo", "alias", "defined?",
})

# Pattern order is correctness-critical (first match wins in alternation):
# - CLASS_VAR before INSTANCE_VAR: prevents @@foo splitting into @ + @foo
# - WORD ends with [?!]? to capture defined?, empty?, save! as single tokens
# - No re.DOTALL: UNKNOWN's . must not match \n (newlines tracked by NEWLINE group)
_MASTER_PATTERN = re.compile(
    r'(?P<NEWLINE>\n)'
    r'|(?P<WHITESPACE>[ \t\r]+)'
    r'|(?P<CLASS_VAR>@@[a-zA-Z_][a-zA-Z0-9_]*)'
    r'|(?P<INSTANCE_VAR>@[a-zA-Z_][a-zA-Z0-9_]*)'
    r'|(?P<GLOBAL_VAR>\$[a-zA-Z_][a-zA-Z0-9_]*)'
    r'|(?P<WORD>[a-zA-Z_][a-zA-Z0-9_]*[?!]?)'
    r'|(?P<COMMENT>#[^\n]*)'
    r'|(?P<UNKNOWN>.)'
)


class Lexer:
    # Known limitations:
    # - name= (method assignment) is not tokenized as a single identifier;
    #   the = would require lookahead conflicting with the assignment operator
    # - String literals are not parsed; their contents are emitted as UNKNOWN tokens
    # - Unicode identifiers are not supported (character classes are ASCII-only)

    def __init__(self, source: str):
        self._source = source

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        line = 1
        line_start = 0  # absolute index of the first char on the current line

        for match in _MASTER_PATTERN.finditer(self._source):
            kind = match.lastgroup
            value = match.group()
            col = match.start() - line_start + 1  # 1-based column of token start

            if kind == 'NEWLINE':
                line += 1
                line_start = match.end()
                continue
            elif kind in ('WHITESPACE', 'COMMENT'):
                continue
            elif kind == 'WORD':
                if value in KEYWORDS:
                    tt = TokenType.KEYWORD
                elif value[0].isupper():
                    tt = TokenType.CONSTANT
                else:
                    tt = TokenType.IDENTIFIER
                tokens.append(Token(tt, value, line, col))
            else:
                tokens.append(Token(TokenType[kind], value, line, col))

        eof_col = len(self._source) - line_start + 1
        tokens.append(Token(TokenType.EOF, '', line, eof_col))
        return tokens
