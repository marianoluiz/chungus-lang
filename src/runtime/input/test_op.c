#include "chungus_runtime.h"

int main()
{
    printf("=== CHUNGUS TYPE PROMOTION EXPERIMENTS ===\n\n");

    ChValue i = ch_int(42);
    ChValue f = ch_float(3.14159);
    ChValue b1 = ch_bool(true);
    b1 = ch_bool(true);
    ChValue b2 = ch_bool(false);
    ChValue s1 = ch_str("hello");
    ChValue s2 = ch_str("");

    printf("int: "); ch_debug_print(i);
    printf("float: ");
    ch_debug_print(f);
    printf("bool true: ");
    ch_debug_print(b1);
    printf("bool false: ");
    ch_debug_print(b2);
    printf("string 'hello': ");
    ch_debug_print(s1);
    printf("string empty: ");
    ch_debug_print(s2);

    // 2. Test ch_to_number promotion
    printf("\n--- TO NUMBER PROMOTION ---\n");
    printf("int 42 → number: %g\n", ch_to_number(i));
    printf("float 3.14159 → number: %g\n", ch_to_number(f));
    printf("bool true → number: %g\n", ch_to_number(b1));
    printf("bool false → number: %g\n", ch_to_number(b2));
    printf("string 'hello' → number: %g\n", ch_to_number(s1));
    printf("string empty → number: %g\n", ch_to_number(s2));

    // 3. Test ch_to_bool promotion (truthiness)
    printf("\n--- TO BOOL PROMOTION (truthiness) ---\n");
    printf("int 42 → bool: %s\n", ch_to_bool(i) ? "true" : "false");
    printf("int 0 → bool: %s\n", ch_to_bool(ch_int(0)) ? "true" : "false");
    printf("float 3.14 → bool: %s\n", ch_to_bool(f) ? "true" : "false");
    printf("float 0.0 → bool: %s\n", ch_to_bool(ch_float(0.0)) ? "true" : "false");
    printf("bool true → bool: %s\n", ch_to_bool(b1) ? "true" : "false");
    printf("bool false → bool: %s\n", ch_to_bool(b2) ? "true" : "false");
    printf("string 'hello' → bool: %s\n", ch_to_bool(s1) ? "true" : "false");
    printf("string empty → bool: %s\n", ch_to_bool(s2) ? "true" : "false");

    // 4. Test arithmetic with promotion
    printf("\n--- ARITHMETIC OPERATIONS ---\n");

    // int + int
    ChValue r1 = ch_add(ch_int(5), ch_int(3));
    printf("5 + 3 = ");
    ch_debug_print(r1);

    // int + float
    ChValue r2 = ch_add(ch_int(5), ch_float(2.5));
    printf("5 + 2.5 = ");
    ch_debug_print(r2);

    // string + int (string promotes to number!)
    ChValue r3 = ch_add(ch_str("hello"), ch_int(10));
    printf("'hello' + 10 = ");
    ch_debug_print(r3);

    // bool + int
    ChValue r4 = ch_add(ch_bool(true), ch_int(5));
    printf("true + 5 = ");
    ch_debug_print(r4);

    // Division (always float)
    ChValue r5 = ch_div(ch_int(10), ch_int(3));
    printf("10 / 3 = ");
    ch_debug_print(r5);


    // Integer division
    ChValue r6 = ch_idiv(ch_int(10), ch_int(3));
    printf("10 // 3 = ");
    ch_debug_print(r6);

    // 5. Test comparisons
    printf("\n--- COMPARISONS ---\n");

    ChValue cmp1 = ch_less(ch_int(5), ch_int(10));
    printf("5 < 10 → ");
    ch_debug_print(cmp1);

    ChValue cmp2 = ch_less(ch_str("hello"), ch_int(1));
    printf("'hello' < 1 → ");
    ch_debug_print(cmp2); // 'hello'→1, 1<1? false

    ChValue cmp3 = ch_eq(ch_bool(true), ch_int(1));
    printf("true == 1 → ");
    ch_debug_print(cmp3); // 1 == 1? true

    // 6. Test logical operations
    printf("\n--- LOGICAL OPERATIONS ---\n");

    ChValue l1 = ch_and(ch_str("hello"), ch_int(42));
    printf("'hello' & 42 → ");
    ch_debug_print(l1); // true && true = true

    ChValue l2 = ch_or(ch_str(""), ch_int(0));
    printf("'' | 0 → ");
    ch_debug_print(l2); // false || false = false

    ChValue l3 = ch_not(ch_str("hello"));
    printf("! 'hello' → ");
    ch_debug_print(l3); // !true = false

    // 7. Check if values are integer-valued
    printf("\n--- IS INT-VALUED ---\n");
    printf("int 42: %s\n", ch_is_int_valued(i) ? "yes" : "no");
    printf("float 3.14: %s\n", ch_is_int_valued(f) ? "yes" : "no");
    printf("float 5.0: %s\n", ch_is_int_valued(ch_float(5.0)) ? "yes" : "no");
    printf("bool true: %s\n", ch_is_int_valued(b1) ? "yes" : "no");
    printf("string 'hello': %s\n", ch_is_int_valued(s1) ? "yes" : "no");

    // Clean up allocated memory
    ch_free(&s1);
    ch_free(&s2);

    return 0;
}