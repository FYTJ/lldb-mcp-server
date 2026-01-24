#include <stdio.h>
#include <stdlib.h>

// Bug: Null pointer dereference
// Expected: AI should identify the null pointer access at line 14

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    int *ptr = NULL;

    printf("About to dereference null pointer...\n");

    // BUG: Dereferencing null pointer
    int value = *ptr;

    printf("Value: %d\n", value);
    return 0;
}
