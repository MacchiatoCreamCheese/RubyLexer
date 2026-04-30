# Ruby Lexer

A lexer for Ruby source code, written in Python. Given a Ruby program as input, it scans the text and produces a flat sequence of typed tokens — the first stage of any compiler or interpreter pipeline.

---

## What is a Lexer?

A **lexer** (also called a *scanner* or *tokenizer*) reads raw source text and breaks it into meaningful units called **tokens**. Each token carries three things: its *type* (what kind of thing it is), its *value* (the exact text from the source), and its *line number* (where it appeared).

For example, the Ruby line:

```ruby
def greet(name)
```

produces these tokens:

```
LINE  TYPE          VALUE
1     KEYWORD       def
1     IDENTIFIER    greet
1     UNKNOWN       (
1     IDENTIFIER    name
1     UNKNOWN       )
```

The lexer does **not** check grammar or meaning — it only classifies. That is the job of a parser, which is out of scope here.

---

## Ruby Identifier Types

Ruby has a rich naming convention where the first character (or a sigil prefix) tells you exactly what kind of name you are looking at. This lexer recognizes all of them.

### Keywords

Reserved words that are part of the Ruby language syntax. They cannot be used as variable names.

```ruby
def  class  end  if  else  elsif  unless  while  until
for  in  do  return  yield  begin  rescue  ensure  raise
true  false  nil  self  super  and  or  not  then
case  when  module  next  break  retry  redo  alias  defined?
```

`defined?` is a special keyword that ends with `?` — it is treated as a single token, not the word `defined` followed by a question mark.

### Identifiers

Local variable names and method names. They start with a lowercase letter or underscore.

```ruby
my_var      # local variable
_private    # underscore prefix — conventional for "private" or unused
count       # simple name

empty?      # method name ending in ? — predicate (returns true/false)
save!       # method name ending in ! — mutating or dangerous version
```

The `?` and `!` suffixes are part of the identifier, not separate tokens.

### Constants

Start with an uppercase letter. Used for class names, module names, and fixed values.

```ruby
MyClass     # class name
MAX_SIZE    # configuration constant (all-caps by convention)
PI          # mathematical constant
```

Ruby enforces that reassigning a constant produces a warning — the uppercase letter is a signal to the programmer.

### Instance Variables

Prefixed with `@`. Belong to a specific object instance. Accessible anywhere within the object's methods.

```ruby
@name       # instance variable
@user_id    # instance variable with underscore
```

### Class Variables

Prefixed with `@@`. Shared across all instances of a class and its subclasses.

```ruby
@@count       # class variable
@@instances   # class variable
```

Class variables must be matched before instance variables in the lexer — otherwise `@@count` would be tokenized as `@` (unknown) followed by `@count` (instance variable), which is wrong.

### Global Variables

Prefixed with `$`. Accessible from anywhere in the program.

```ruby
$global     # user-defined global
$DEBUG      # Ruby built-in global flag
```

---

## How It Works

The lexer lives in `ruby_lexer/lexer.py` and is built around three ideas.

### 1. A Single Master Regex

All token patterns are combined into one regular expression using named groups and the alternation operator `|`. Python's `re.finditer` scans the source left-to-right, and at each position tries each alternative in order — the first one that matches wins.

```python
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
```

The order of alternatives is not cosmetic — it is correctness-critical:

- **`CLASS_VAR` before `INSTANCE_VAR`**: both patterns start with `@`. If `INSTANCE_VAR` came first, `@@count` would match `@` as an unknown character, then `@count` as an instance variable. With `CLASS_VAR` first, `@@count` is consumed in one match.
- **`WORD` ends with `[?!]?`**: the optional suffix captures `defined?`, `empty?`, and `save!` as single tokens. Without it, `defined?` would become the identifier `defined` plus the unknown character `?`, and `defined?` would never be recognized as a keyword.
- **`UNKNOWN` is `.` without `re.DOTALL`**: the dot does not match newlines by default. Newlines are handled exclusively by the `NEWLINE` group so they can be counted for line tracking.

### 2. Line Tracking

A `line` counter starts at 1. The `NEWLINE` group matches every `\n` but does not emit a token — it just increments the counter. Every token that *is* emitted receives the current value of `line`.

```python
if kind == 'NEWLINE':
    line += 1
    continue   # not emitted
```

Whitespace and Ruby line comments are also skipped instead of being emitted as tokens:

```python
elif kind in ('WHITESPACE', 'COMMENT'):
    continue
```

### 3. Post-Processing WORD Matches

Keywords and identifiers share the same character set, so they are captured by one pattern (`WORD`) and distinguished afterwards:

```python
elif kind == 'WORD':
    if value in KEYWORDS:
        tt = TokenType.KEYWORD
    elif value[0].isupper():
        tt = TokenType.CONSTANT
    else:
        tt = TokenType.IDENTIFIER
```

`KEYWORDS` is a `frozenset` for O(1) membership lookup. If the value is not a keyword, an uppercase first character means it is a constant; otherwise it is an identifier.

### Token Dataclass

Each token is a simple immutable record:

```python
@dataclass
class Token:
    type: TokenType   # one of the TokenType enum values
    value: str        # exact text from the source
    line: int         # 1-based line number
```

The `@dataclass` decorator gives free `__eq__` comparison, which makes test assertions straightforward.

### Known Limitations

- **Method assignment (`name=`)** is not tokenized as a single identifier. Recognizing it would require lookahead that conflicts with treating `=` as the assignment operator.
- **String literals** are not parsed. A string like `"hello"` produces several `UNKNOWN` tokens (the quotes and each character). Ruby line comments starting with `#` are recognized and skipped.
- **Unicode identifiers** are not supported. The character classes in the regex are ASCII-only.

---

## Project Structure

```
RubyLexer/
└── ruby_lexer/
    ├── lexer.py        # TokenType enum, Token dataclass, Lexer class
    ├── main.py         # CLI entry point
    └── test_lexer.py   # unittest suite (10 test cases)
```

No third-party packages are required. The project uses only the Python standard library (`re`, `enum`, `dataclasses`, `argparse`, `unittest`).

---

## How to Run

**Requirements:** Python 3.7 or later.

### Run the tests

```bash
cd ruby_lexer
python -m unittest test_lexer.py -v
```

Expected output:

```
test_class_var_not_instance_var ... ok
test_class_vars ... ok
test_constants ... ok
test_defined_keyword ... ok
test_global_vars ... ok
test_instance_vars ... ok
test_keywords ... ok
test_local_variables ... ok
test_method_suffixes ... ok
test_multiline_snippet ... ok

Ran 10 tests in 0.001s

OK
```

### Tokenize a Ruby file

```bash
python ruby_lexer/main.py path/to/file.rb
```

### Tokenize an inline string

```bash
python ruby_lexer/main.py -e "def greet(name)"
```

### Example

Given this Ruby snippet:

```ruby
def greet(name)
  @msg = @@prefix + $sep + name
  puts msg if valid?
end
```

Running `python ruby_lexer/main.py -e "..."` produces:

```
LINE  TYPE          VALUE
----------------------------------------
1     KEYWORD       def
1     IDENTIFIER    greet
1     UNKNOWN       (
1     IDENTIFIER    name
1     UNKNOWN       )
2     INSTANCE_VAR  @msg
2     UNKNOWN       =
2     CLASS_VAR     @@prefix
2     UNKNOWN       +
2     GLOBAL_VAR    $sep
2     UNKNOWN       +
2     IDENTIFIER    name
3     IDENTIFIER    puts
3     IDENTIFIER    msg
3     KEYWORD       if
3     IDENTIFIER    valid?
4     KEYWORD       end
4     EOF
```
