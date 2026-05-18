#ifndef LEXER_H
#define LEXER_H

#include <stddef.h>

#define MAX_TOKEN_LEN 256

typedef enum {
    TOK_KEYWORD,
    TOK_IDENTIFIER,
    TOK_CONSTANT,
    TOK_INSTANCE_VAR,
    TOK_CLASS_VAR,
    TOK_GLOBAL_VAR,
    TOK_UNKNOWN,
    TOK_EOF
} TokenType;

typedef struct {
    TokenType type;
    char      value[MAX_TOKEN_LEN];
    int       line;
    int       col;
} Token;

typedef struct {
    Token  *items;
    size_t  count;
    size_t  capacity;
} TokenList;

TokenList tokenize(const char *source);
void token_list_free(TokenList *list);
const char *token_type_name(TokenType t);

#endif
