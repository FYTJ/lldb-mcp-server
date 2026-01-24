#include <stdio.h>
#include <string.h>

// Bug: Stack buffer overflow
// Expected: AI should identify buffer overflow on line 16

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    char buffer[16];
    const char *input = "This string is way too long for the buffer!";

    printf("Buffer size: 16, Input length: %lu\n", strlen(input));

    // BUG: Buffer overflow - strcpy doesn't check bounds
    strcpy(buffer, input);

    printf("Buffer: %s\n", buffer);
    return 0;
}
