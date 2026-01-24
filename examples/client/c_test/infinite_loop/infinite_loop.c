#include <stdio.h>

// Bug: Infinite loop due to logic error
// Expected: AI should identify the infinite loop condition on line 15

int main(int argc, char *argv[]) {
    (void)argc;
    (void)argv;

    int counter = 0;
    int target = 10;

    printf("Starting loop, target: %d\n", target);

    // BUG: Infinite loop - counter never increments correctly
    while (counter < target) {
        printf("Counter: %d\n", counter);
        // Bug: Should be counter++ but using counter-- causes infinite loop
        counter--;
    }

    printf("Loop completed!\n");
    return 0;
}
