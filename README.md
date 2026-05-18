# Ruby Lexer

A lexer for Ruby source code, written in C as a finite state machine. Given a Ruby program as input, it scans the text and produces a flat sequence of typed tokens — the first stage of any compiler or interpreter pipeline.

The lexer is hand-written: no regex, no third-party library. It recognizes the language with an explicit state machine driven by a `switch`, scanning the source one character at a time.

---

## What is a Lexer?

A **lexer** (also called a *scanner* or *tokenizer*) reads raw source text and breaks it into meaningful units called **tokens**. Each token carries four things: its *type* (what kind of thing it is), its *value* (the exact text from the source), its *line*, and its *column* (where it appeared).

For example, the Ruby line:

```ruby
def greet(name)
```

produces these tokens:

```
LINE  COL   TYPE          VALUE
1     1     KEYWORD       def
1     5     IDENTIFIER    greet
1     10    UNKNOWN       (
1     11    IDENTIFIER    name
1     15    UNKNOWN       )
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
my_var
_private
count

empty?
save!
```

The `?` and `!` suffixes are part of the identifier, not separate tokens.

### Constants

Start with an uppercase letter. Used for class names, module names, and fixed values.

```ruby
MyClass
MAX_SIZE
PI
```

### Instance Variables

Prefixed with `@`. Belong to a specific object instance.

```ruby
@name
@user_id
```

### Class Variables

Prefixed with `@@`. Shared across all instances of a class and its subclasses.

```ruby
@@count
@@instances
```

`@@` must be recognized before `@` — otherwise `@@count` would be tokenized as `@` followed by an instance variable `@count`, which is wrong.

### Global Variables

Prefixed with `$`. Accessible from anywhere in the program.

```ruby
$global
$DEBUG
```

---

## How It Works

The lexer is a **finite state machine**. Instead of matching patterns with a regex engine, it keeps a current *state*, reads one character at a time, and decides what to do based on that state and that character.

### The States

```c
typedef enum {
    ST_START,
    ST_IN_WORD,
    ST_IN_IVAR,
    ST_IN_CVAR,
    ST_IN_GVAR,
    ST_IN_COMMENT
} LexerState;
```

The scanner starts in `ST_START`. Looking at the next character, it transitions into one of the other states, which then consume characters until the token is complete — at which point it returns to `ST_START`.

### The Scan Loop

`tokenize()` walks the source with a `switch (state)` inside a loop:

- **`ST_START`** — inspect the current character and decide:
  - newline → advance line counter, reset column to 1
  - space / tab / `\r` → skip
  - `#` → enter `ST_IN_COMMENT`
  - `@` → look ahead one character; a second `@` means `ST_IN_CVAR`, otherwise `ST_IN_IVAR`
  - `$` → enter `ST_IN_GVAR`
  - letter or `_` → enter `ST_IN_WORD`
  - anything else → emit a one-character `UNKNOWN` token

- **`ST_IN_WORD`** — accumulate letters, digits, and underscores, then allow one optional `?` or `!`. When the word ends it is classified: a keyword becomes `KEYWORD`, an uppercase first letter makes it a `CONSTANT`, otherwise it is an `IDENTIFIER`.

- **`ST_IN_IVAR` / `ST_IN_CVAR` / `ST_IN_GVAR`** — accumulate identifier characters after the sigil, then emit the matching token type.

- **`ST_IN_COMMENT`** — consume everything up to (but not including) the newline, emitting no token at all. The newline itself is handled by `ST_START`, so the line counter still advances correctly.

### Line and Column Tracking

The scanner keeps a 1-based `line` and `col` as it advances. Every time it passes a `\n`, `line` increments and `col` resets to 1; otherwise `col` increments. When a token begins, its starting line and column are recorded and stored on the token.

### Tokens

Each token is a simple record:

```c
typedef struct {
    TokenType type;
    char      value[MAX_TOKEN_LEN];
    int       line;
    int       col;
} Token;
```

`tokenize()` returns a `TokenList` — a growable array that doubles its capacity as needed — terminated by a final `EOF` token.

### Known Limitations

- **Method assignment (`name=`)** is not tokenized as a single identifier; the `=` is treated as a separate operator.
- **String literals** are not parsed — their characters become `UNKNOWN` tokens. Ruby `#` line comments *are* recognized and skipped.
- **Unicode identifiers** are not supported; the character classes are ASCII-only.

---

## Project Structure

```
RubyLexer/
└── c_lexer/
    ├── lexer.h
    ├── lexer.c
    ├── main.c
    └── test.rb
```

Pure C99, standard library only (`stdio.h`, `stdlib.h`, `string.h`, `ctype.h`).

---

## How to Build and Run

**Requirements:** any C99 compiler (`gcc`, `clang`, or MSVC `cl`).

### Build the CLI

```bash
cd c_lexer
gcc -std=c99 -Wall -Wextra -o rubylex lexer.c main.c
```

### Run it on the sample file

The repository includes `test.rb`, a sample Ruby file that exercises every
token type. Tokenize it with:

```bash
./rubylex test.rb
```

You can also tokenize any other file, or an inline string:

```bash
./rubylex path/to/file.rb
./rubylex -e "def greet(name)"
```

### Example

`test.rb` contains:

```ruby
# This is a comment
class MyClass
  def initialize(name)
    @name = name
    @@count += 1
    $debug = false # This is a comment
  end
end
```

Running `./rubylex test.rb` produces:

```
LINE  COL   TYPE          VALUE
----------------------------------------------
2     1     KEYWORD       class
2     7     CONSTANT      MyClass
3     3     KEYWORD       def
3     7     IDENTIFIER    initialize
3     17    UNKNOWN       (
3     18    IDENTIFIER    name
3     22    UNKNOWN       )
4     5     INSTANCE_VAR  @name
4     11    UNKNOWN       =
4     13    IDENTIFIER    name
5     5     CLASS_VAR     @@count
5     13    UNKNOWN       +
5     14    UNKNOWN       =
5     16    UNKNOWN       1
6     5     GLOBAL_VAR    $debug
6     12    UNKNOWN       =
6     14    KEYWORD       false
7     3     KEYWORD       end
8     1     KEYWORD       end
8     4     EOF
```

Every name gets a token — keyword, identifier, constant, instance/class/global
variable — tagged with the line and column where it starts. The two comments
produce no tokens. Operators and punctuation become `UNKNOWN`, so `+=` shows up
as a `+` token followed by a `=` token.
