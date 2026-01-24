#include <stdio.h>

// Bug: Division by zero
// Expected: AI should identify division by zero on line 17

int calculate(int a, int b) {
    return a / b;
}

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    int numerator = 100;
    int denominator = 0;

    printf("Calculating %d / %d\n", numerator, denominator);

    // BUG: Division by zero
    int result = calculate(numerator, denominator);

    printf("Result: %d\n", result);
    return 0;
}
