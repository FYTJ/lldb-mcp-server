#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Bug: Double free
// Expected: AI should identify double free on line 25

void process_data(char *data) {
    printf("Processing: %s\n", data);
    // First free - this is correct
    free(data);
}

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    char *buffer = (char *)malloc(64);
    if (!buffer) {
        return 1;
    }

    strcpy(buffer, "Important data");

    process_data(buffer);

    // BUG: Double free - buffer was already freed in process_data()
    free(buffer);

    return 0;
}
