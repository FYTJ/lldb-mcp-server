#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Bug: Use after free
// Expected: AI should identify use-after-free on line 20

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    char *buffer = (char *)malloc(32);
    if (!buffer) {
        return 1;
    }

    strcpy(buffer, "Hello, World!");
    printf("Before free: %s\n", buffer);

    free(buffer);

    // BUG: Use after free - accessing freed memory
    printf("After free: %s\n", buffer);

    return 0;
}
