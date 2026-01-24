#include <stdio.h>

// Bug: Stack overflow due to infinite recursion
// Expected: AI should identify the missing base case on line 10

int recursive_function(int n) {
    printf("Recursion depth: %d\n", n);

    // BUG: No proper base case - causes stack overflow
    // Should check if n <= 0 and return
    return recursive_function(n + 1);
}

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    printf("Starting recursive function...\n");

    // This will cause stack overflow
    int result = recursive_function(0);

    printf("Result: %d\n", result);
    return 0;
}
