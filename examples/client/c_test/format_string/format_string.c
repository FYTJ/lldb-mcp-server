#include <stdio.h>
#include <string.h>

// Bug: Format string vulnerability
// Expected: AI should identify format string vulnerability on line 19

void log_message(const char *msg) {
    // BUG: Format string vulnerability - user input used directly as format string
    printf(msg);
    printf("\n");
}

int main(int argc, char *argv[]) {
    (void)argc;

    char user_input[256];

    // Simulate user input with format specifiers
    if (argv[1]) {
        strncpy(user_input, argv[1], sizeof(user_input) - 1);
        user_input[sizeof(user_input) - 1] = '\0';
    } else {
        // Default malicious input for demonstration
        strcpy(user_input, "%p %p %p %p");
    }

    printf("Logging user message...\n");

    // BUG: Passing user-controlled string directly to printf
    log_message(user_input);

    return 0;
}
