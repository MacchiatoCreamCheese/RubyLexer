#include "lexer.h"

#include <stdio.h>
#include <stdlib.h>

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    long size;
    char *buf;
    size_t read;

    if (!f) {
        return NULL;
    }
    fseek(f, 0, SEEK_END);
    size = ftell(f);
    fseek(f, 0, SEEK_SET);
    if (size < 0) {
        fclose(f);
        return NULL;
    }
    buf = malloc((size_t)size + 1);
    if (!buf) {
        fclose(f);
        return NULL;
    }
    read = fread(buf, 1, (size_t)size, f);
    buf[read] = '\0';
    fclose(f);
    return buf;
}

static void print_table(const TokenList *list) {
    size_t i;
    printf("%-6s%-6s%-14s%s\n", "LINE", "COL", "TYPE", "VALUE");
    printf("----------------------------------------------\n");
    for (i = 0; i < list->count; i++) {
        const Token *t = &list->items[i];
        printf("%-6d%-6d%-14s%s\n",
               t->line, t->col, token_type_name(t->type), t->value);
    }
}

int main(int argc, char *argv[]) {
    char *source = NULL;
    int free_source = 0;
    TokenList tokens;

    if (argc == 3 && argv[1][0] == '-' && argv[1][1] == 'e' && argv[1][2] == '\0') {
        source = argv[2];
    } else if (argc == 2 && argv[1][0] != '-') {
        source = read_file(argv[1]);
        if (!source) {
            fprintf(stderr, "Error: cannot read file '%s'\n", argv[1]);
            return 1;
        }
        free_source = 1;
    } else {
        fprintf(stderr, "Usage: %s <file.rb>\n", argv[0]);
        fprintf(stderr, "       %s -e \"ruby code\"\n", argv[0]);
        return 1;
    }

    tokens = tokenize(source);
    print_table(&tokens);

    token_list_free(&tokens);
    if (free_source) {
        free(source);
    }
    return 0;
}
