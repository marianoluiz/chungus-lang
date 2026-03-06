/**
 * Test program for CHUNGUS runtime library
 * Demonstrates type promotion and dynamic operations
 */

#include "chungus_runtime.h"

int main() {
    printf("=== CHUNGUS Runtime Library Test ===\n\n");
    
    // Test 1: Basic constructors
    printf("=== Test 1: Constructors ===\n");
    ChValue a = ch_int(42);
    ChValue b = ch_float(3.14);
    ChValue c = ch_bool(true);
    ChValue d = ch_str("hello");
    
    printf("int:    "); ch_debug_print(a);
    printf("float:  "); ch_debug_print(b);
    printf("bool:   "); ch_debug_print(c);
    printf("string: "); ch_debug_print(d);
    printf("\n");
    
    // Test 2: Type promotion
    printf("=== Test 2: Type Promotion ===\n");
    printf("ch_to_number(42) = %g\n", ch_to_number(a));
    printf("ch_to_number(3.14) = %g\n", ch_to_number(b));
    printf("ch_to_number(true) = %g\n", ch_to_number(c));
    printf("ch_to_number(\"hello\") = %g\n", ch_to_number(d));
    printf("\n");
    
    printf("ch_to_bool(42) = %s\n", ch_to_bool(a) ? "true" : "false");
    printf("ch_to_bool(0) = %s\n", ch_to_bool(ch_int(0)) ? "true" : "false");
    printf("ch_to_bool(3.14) = %s\n", ch_to_bool(b) ? "true" : "false");
    printf("ch_to_bool(\"\") = %s\n", ch_to_bool(ch_str("")) ? "true" : "false");
    printf("\n");
    
    // Test 3: Arithmetic operations
    printf("=== Test 3: Arithmetic Operations ===\n");
    ChValue x = ch_int(10);
    ChValue y = ch_int(3);
    
    printf("10 + 3 = "); ch_debug_print(ch_add(x, y));
    printf("10 - 3 = "); ch_debug_print(ch_sub(x, y));
    printf("10 * 3 = "); ch_debug_print(ch_mul(x, y));
    printf("10 / 3 = "); ch_debug_print(ch_div(x, y));
    printf("10 // 3 = "); ch_debug_print(ch_idiv(x, y));
    printf("10 %% 3 = "); ch_debug_print(ch_mod(x, y));
    printf("10 ** 3 = "); ch_debug_print(ch_pow(x, y));
    printf("\n");
    
    // Test 4: Type coercion in arithmetic
    printf("=== Test 4: Type Coercion in Arithmetic ===\n");
    ChValue int_val = ch_int(5);
    ChValue float_val = ch_float(2.5);
    ChValue bool_val = ch_bool(true);
    
    printf("5 + 2.5 = "); ch_debug_print(ch_add(int_val, float_val));
    printf("5 + true = "); ch_debug_print(ch_add(int_val, bool_val));
    printf("true + true = "); ch_debug_print(ch_add(bool_val, bool_val));
    printf("\n");
    
    // Test 5: Comparison operations
    printf("=== Test 5: Comparison Operations ===\n");
    printf("10 < 3 = "); ch_debug_print(ch_less(x, y));
    printf("10 > 3 = "); ch_debug_print(ch_greater(x, y));
    printf("10 == 10 = "); ch_debug_print(ch_eq(x, ch_int(10)));
    printf("10 != 3 = "); ch_debug_print(ch_ne(x, y));
    printf("\n");
    
    // Test 6: Logical operations
    printf("=== Test 6: Logical Operations ===\n");
    ChValue t = ch_bool(true);
    ChValue f = ch_bool(false);
    
    printf("true & false = "); ch_debug_print(ch_and(t, f));
    printf("true | false = "); ch_debug_print(ch_or(t, f));
    printf("!true = "); ch_debug_print(ch_not(t));
    printf("!false = "); ch_debug_print(ch_not(f));
    printf("\n");
    
    // Test 7: 1D Arrays
    printf("=== Test 7: 1D Arrays ===\n");
    ChValue arr1d = ch_array_1d(5);
    ch_array_set_1d(&arr1d, 0, ch_int(10));
    ch_array_set_1d(&arr1d, 1, ch_float(3.14));
    ch_array_set_1d(&arr1d, 2, ch_str("test"));
    
    printf("arr[0] = "); ch_debug_print(ch_array_get_1d(arr1d, 0));
    printf("arr[1] = "); ch_debug_print(ch_array_get_1d(arr1d, 1));
    printf("arr[2] = "); ch_debug_print(ch_array_get_1d(arr1d, 2));
    printf("\n");
    
    // Test 8: 2D Arrays
    printf("=== Test 8: 2D Arrays ===\n");
    ChValue arr2d = ch_array_2d(3, 3);
    ch_array_set_2d(&arr2d, 0, 0, ch_int(1));
    ch_array_set_2d(&arr2d, 1, 1, ch_int(5));
    ch_array_set_2d(&arr2d, 2, 2, ch_int(9));
    
    printf("matrix[0][0] = "); ch_debug_print(ch_array_get_2d(arr2d, 0, 0));
    printf("matrix[1][1] = "); ch_debug_print(ch_array_get_2d(arr2d, 1, 1));
    printf("matrix[2][2] = "); ch_debug_print(ch_array_get_2d(arr2d, 2, 2));
    printf("\n");
    
    // Test 9: CHUNGUS sample program
    printf("=== Test 9: CHUNGUS Sample (x=42, y=10, result=x+y) ===\n");
    ChValue ch_x = ch_int(42);
    ChValue ch_y = ch_int(10);
    ChValue ch_result = ch_add(ch_x, ch_y);
    
    printf("x = "); ch_print(ch_x); printf("\n");
    printf("y = "); ch_print(ch_y); printf("\n");
    printf("result = "); ch_print(ch_result); printf("\n");
    printf("\n");
    
    // Cleanup
    ch_free(&d);
    ch_free(&arr1d);
    ch_free(&arr2d);
    
    printf("=== All tests completed! ===\n");
    
    return 0;
}
