
#include "lexer.h"

#include <ctype.h>
#include <stdlib.h>
#include <string.h>

static const char *KEYWORDS[] = {
    "def", "class", "end", "if", "else", "elsif", "unless",
    "while", "until", "for", "in", "do", "return", "yield",
    "begin", "rescue", "ensure", "raise", "true", "false",
    "nil", "self", "super", "and", "or", "not", "then",
    "case", "when", "module", "next", "break", "retry",
    "redo", "alias", "defined?"
};
static const size_t KEYWORD_COUNT = sizeof(KEYWORDS) / sizeof(KEYWORDS[0]);

static int is_keyword(const char *word) {
    size_t i;
    for (i = 0; i < KEYWORD_COUNT; i++) {
        if (strcmp(word, KEYWORDS[i]) == 0) {
            return 1;
        }
    }
    return 0;
}

static TokenType classify_word(const char *word) {
    if (is_keyword(word)) {
        return TOK_KEYWORD;
    }
    if (isupper((unsigned char)word[0])) {
        return TOK_CONSTANT;
    }
    return TOK_IDENTIFIER;
}


static void push_token(TokenList *list, TokenType type,
                        const char *value, int line, int col) {
    Token *tok;
    if (list->count == list->capacity) {
        list->capacity = list->capacity ? list->capacity * 2 : 16;
        list->items = realloc(list->items, list->capacity * sizeof(Token));
    }
    tok = &list->items[list->count++];
    tok->type = type;
    strncpy(tok->value, value, MAX_TOKEN_LEN - 1);
    tok->value[MAX_TOKEN_LEN - 1] = '\0';
    tok->line = line;
    tok->col = col;
}

void token_list_free(TokenList *list) {
    free(list->items);
    list->items = NULL;
    list->count = 0;
    list->capacity = 0;
}

const char *token_type_name(TokenType t) {
    switch (t) {
        case TOK_KEYWORD:      return "KEYWORD";
        case TOK_IDENTIFIER:   return "IDENTIFIER";
        case TOK_CONSTANT:     return "CONSTANT";
        case TOK_INSTANCE_VAR: return "INSTANCE_VAR";
        case TOK_CLASS_VAR:    return "CLASS_VAR";
        case TOK_GLOBAL_VAR:   return "GLOBAL_VAR";
        case TOK_UNKNOWN:      return "UNKNOWN";
        case TOK_EOF:          return "EOF";
    }
    return "?";
}

typedef enum {
    ST_START,   
    ST_IN_WORD,   
    ST_IN_IVAR,
    ST_IN_CVAR,    
    ST_IN_GVAR, 
    ST_IN_COMMENT 
} LexerState;

static int is_ident_char(char c) {
    return isalnum((unsigned char)c) || c == '_';
}

TokenList tokenize(const char *source) {
    TokenList list = { NULL, 0, 0 };
    LexerState state = ST_START;
    int line = 1, col = 1;        
    int start_line = 1, start_col = 1;
    char buf[MAX_TOKEN_LEN];
    int len = 0;           
    size_t i = 0;

    while (source[i] != '\0' || state != ST_START) {
        char c = source[i];

        switch (state) {
        case ST_START:
            if (c == '\n') {
                i++; line++; col = 1;
            } else if (c == ' ' || c == '\t' || c == '\r') {
                i++; col++;
            } else if (c == '#') {
                i++; col++;
                state = ST_IN_COMMENT;
            } else if (c == '@') {
                start_line = line; start_col = col;
                buf[0] = '@'; len = 1;
                i++; col++;
                if (source[i] == '@') {  
                    buf[1] = '@'; len = 2;
                    i++; col++;
                    state = ST_IN_CVAR;
                } else {             
                    state = ST_IN_IVAR;
                }
            } else if (c == '$') {
                start_line = line; start_col = col;
                buf[0] = '$'; len = 1;
                i++; col++;
                state = ST_IN_GVAR;
            } else if (isalpha((unsigned char)c) || c == '_') {
                start_line = line; start_col = col;
                len = 0;
                state = ST_IN_WORD;     
            } else {
                buf[0] = c; buf[1] = '\0';
                push_token(&list, TOK_UNKNOWN, buf, line, col);
                i++; col++;
            }
            break;

        case ST_IN_WORD:
            if (is_ident_char(c)) {
                if (len < MAX_TOKEN_LEN - 1) buf[len++] = c;
                i++; col++;
            } else if (c == '?' || c == '!') {
                if (len < MAX_TOKEN_LEN - 1) buf[len++] = c;
                i++; col++;
                buf[len] = '\0';
                push_token(&list, classify_word(buf), buf,
                           start_line, start_col);
                state = ST_START;
            } else {
                buf[len] = '\0';
                push_token(&list, classify_word(buf), buf,
                           start_line, start_col);
                state = ST_START;      
            }
            break;

        case ST_IN_IVAR:
        case ST_IN_CVAR:
        case ST_IN_GVAR:
            if (is_ident_char(c)) {
                if (len < MAX_TOKEN_LEN - 1) buf[len++] = c;
                i++; col++;
            } else {
                int sigil_len = (state == ST_IN_CVAR) ? 2 : 1;
                if (len == sigil_len) {
                    int k;
                    for (k = 0; k < len; k++) {
                        char one[2];
                        one[0] = buf[k]; one[1] = '\0';
                        push_token(&list, TOK_UNKNOWN, one,
                                   start_line, start_col + k);
                    }
                } else {
                    TokenType tt = (state == ST_IN_IVAR) ? TOK_INSTANCE_VAR
                                 : (state == ST_IN_CVAR) ? TOK_CLASS_VAR
                                 : TOK_GLOBAL_VAR;
                    buf[len] = '\0';
                    push_token(&list, tt, buf, start_line, start_col);
                }
                state = ST_START; 
            }
            break;

        case ST_IN_COMMENT:
            if (c == '\n' || c == '\0') {
                state = ST_START;
            } else {
                i++; col++;
            }
            break;
        }
    }

    push_token(&list, TOK_EOF, "", line, col);
    return list;
}
