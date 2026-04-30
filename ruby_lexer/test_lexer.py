import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lexer import Lexer, Token, TokenType, KEYWORDS


def tokenize(source):
    return Lexer(source).tokenize()


def data_tokens(tokens):
    """Return all tokens except the trailing EOF."""
    return [t for t in tokens if t.type != TokenType.EOF]


class TestLexer(unittest.TestCase):

    def test_local_variables(self):
        tokens = data_tokens(tokenize("my_var _private x"))
        self.assertEqual(len(tokens), 3)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.IDENTIFIER)
        self.assertEqual([t.value for t in tokens], ["my_var", "_private", "x"])

    def test_method_suffixes(self):
        tokens = data_tokens(tokenize("empty? save!"))
        self.assertEqual(len(tokens), 2)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[0].value, "empty?")
        self.assertEqual(tokens[1].value, "save!")

    def test_constants(self):
        tokens = data_tokens(tokenize("MyClass MAX_SIZE PI"))
        self.assertEqual(len(tokens), 3)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.CONSTANT)
        self.assertEqual([t.value for t in tokens], ["MyClass", "MAX_SIZE", "PI"])

    def test_instance_vars(self):
        tokens = data_tokens(tokenize("@name @user_id"))
        self.assertEqual(len(tokens), 2)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.INSTANCE_VAR)
        self.assertEqual(tokens[0].value, "@name")
        self.assertEqual(tokens[1].value, "@user_id")

    def test_class_vars(self):
        tokens = data_tokens(tokenize("@@count @@instances"))
        self.assertEqual(len(tokens), 2)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.CLASS_VAR)
        self.assertEqual(tokens[0].value, "@@count")
        self.assertEqual(tokens[1].value, "@@instances")

    def test_global_vars(self):
        tokens = data_tokens(tokenize("$global $DEBUG"))
        self.assertEqual(len(tokens), 2)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.GLOBAL_VAR)
        self.assertEqual(tokens[0].value, "$global")
        self.assertEqual(tokens[1].value, "$DEBUG")

    def test_keywords(self):
        tokens = data_tokens(tokenize("def end if class"))
        self.assertEqual(len(tokens), 4)
        for tok in tokens:
            self.assertEqual(tok.type, TokenType.KEYWORD)
        self.assertEqual([t.value for t in tokens], ["def", "end", "if", "class"])

    def test_defined_keyword(self):
        # defined? must be captured as a single KEYWORD token, not IDENTIFIER + UNKNOWN
        tokens = data_tokens(tokenize("defined?"))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.KEYWORD)
        self.assertEqual(tokens[0].value, "defined?")

    def test_multiline_snippet(self):
        # Verifies token types, line numbers, and column positions
        source = "def foo\n  @bar = @@baz\n  $qux\nend\n"
        tokens = tokenize(source)

        expected = [
            Token(TokenType.KEYWORD,      "def",     1, 1),
            Token(TokenType.IDENTIFIER,   "foo",     1, 5),
            Token(TokenType.INSTANCE_VAR, "@bar",    2, 3),
            Token(TokenType.UNKNOWN,      "=",       2, 8),
            Token(TokenType.CLASS_VAR,    "@@baz",   2, 10),
            Token(TokenType.GLOBAL_VAR,   "$qux",    3, 3),
            Token(TokenType.KEYWORD,      "end",     4, 1),
            Token(TokenType.EOF,          "",        5, 1),
        ]
        self.assertEqual(tokens, expected)

    def test_class_var_not_instance_var(self):
        # @@count must produce exactly one CLASS_VAR token, not @ + @count
        tokens = data_tokens(tokenize("@@count"))
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.CLASS_VAR)
        self.assertEqual(tokens[0].value, "@@count")

    def test_comment_own_line(self):
        tokens = data_tokens(tokenize("# this is a comment\nmy_var = 1"))
        values = [t.value for t in tokens]
        for word in ("this", "is", "a", "comment"):
            self.assertNotIn(word, values)
        self.assertEqual(tokens[0].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[0].value, "my_var")
        self.assertEqual(tokens[0].line, 2)
        self.assertEqual(tokens[0].col, 1)

    def test_inline_comment(self):
        tokens = data_tokens(tokenize("x = 1 # set x\ny = 2"))
        line2 = [t for t in tokens if t.line == 2]
        self.assertEqual(len(line2), 3)  # y, =, 2
        self.assertEqual(line2[0].value, "y")
        self.assertEqual(line2[0].col, 1)
        self.assertEqual(line2[0].line, 2)

    def test_column_accuracy(self):
        tokens = data_tokens(tokenize("def foo"))
        self.assertEqual(tokens[0].type, TokenType.KEYWORD)
        self.assertEqual(tokens[0].value, "def")
        self.assertEqual(tokens[0].col, 1)
        self.assertEqual(tokens[1].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[1].value, "foo")
        self.assertEqual(tokens[1].col, 5)

    def test_comment_with_identifier_content(self):
        tokens = data_tokens(tokenize("# hello world\nreal_var"))
        values = [t.value for t in tokens]
        self.assertNotIn("hello", values)
        self.assertNotIn("world", values)
        self.assertEqual(len(tokens), 1)
        self.assertEqual(tokens[0].type, TokenType.IDENTIFIER)
        self.assertEqual(tokens[0].value, "real_var")
        self.assertEqual(tokens[0].line, 2)
        self.assertEqual(tokens[0].col, 1)


if __name__ == '__main__':
    unittest.main()
