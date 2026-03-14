/**
 * CHUNGUS Runtime Library - Header
 * 
 * Dynamic type system with CHUNGUS-specific coercion rules.
 * Supports: int, float, bool, string, array (1D and 2D)
 */

#ifndef CHUNGUS_RUNTIME_H
#define CHUNGUS_RUNTIME_H

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <math.h>
#include <stdint.h>

// Forward declaration
typedef struct ChValue ChValue;

// Type tags matching CHUNGUS semantic analyzer
typedef enum {
    TY_INT,
    TY_FLOAT,
    TY_BOOL,
    TY_STRING,
    TY_ARRAY
} ChType;

// Dynamic value container
typedef struct ChValue {
    ChType type;
    
    union {
        int64_t i;
        double f;
        bool b;
        char* s;
        
        // Array: can hold heterogeneous elements
        struct {
            size_t len;      // Total elements (rows * cols for 2D)
            size_t rows;     // Number of rows (1 for 1D arrays)
            size_t cols;     // Number of columns (length for 1D arrays)
            ChValue* items;  // Flat array of elements
        } arr;
    };
} ChValue;


// ============================================================================
// CONSTRUCTORS
// ============================================================================

ChValue ch_int(int64_t x);
ChValue ch_float(double x);
ChValue ch_bool(bool x);
ChValue ch_str(const char* x);
ChValue ch_array_1d(size_t size);
ChValue ch_array_2d(size_t rows, size_t cols);


// ============================================================================
// TYPE PROMOTION (CHUNGUS Coercion Rules)
// ============================================================================

// Promote to number for arithmetic/relational operations
// Semantic conversion rules:
//   - int: integer value
//   - float: float value
//   - bool: true→1, false→0 (integer values)
//   - string: non-empty→1, empty→0 (integer values)
//   - array: error (returns 0)
// Returns: double (for computation convenience)
double ch_to_number(ChValue v);

// Promote to boolean for logical operations and conditionals
// Conversion rules:
//   - bool: actual value
//   - int: non-zero→true, zero→false
//   - float: non-zero→true, zero→false
//   - string: non-empty→true, empty→false
//   - array: non-empty→true, empty→false
bool ch_to_bool(ChValue v);

// Check if value is integer after promotion
bool ch_is_int_valued(ChValue v);

// Runtime validators for array dimensions/indices
// - ch_to_array_size_checked: must be positive whole number (>= 1)
// - ch_to_index_checked: must be non-negative whole number (>= 0)
// On invalid input, prints runtime error and terminates execution.
size_t ch_to_array_size_checked(ChValue v, const char* context);
int ch_to_index_checked(ChValue v, const char* context);


// ============================================================================
// ARITHMETIC OPERATIONS (CHUNGUS Coercion Rules)
// ============================================================================

// All arithmetic ops promote both operands to number
// Result type rules:
//   - "/" (division) always returns TY_FLOAT
//   - If either operand is TY_FLOAT → result is TY_FLOAT
//   - Otherwise (both int-like: TY_INT, TY_BOOL, TY_STRING) → result is TY_INT

ChValue ch_add(ChValue left, ChValue right);      // +
ChValue ch_sub(ChValue left, ChValue right);      // -
ChValue ch_mul(ChValue left, ChValue right);      // *
ChValue ch_div(ChValue left, ChValue right);      // / (always float)
ChValue ch_idiv(ChValue left, ChValue right);     // // (integer division)
ChValue ch_mod(ChValue left, ChValue right);      // %
ChValue ch_pow(ChValue left, ChValue right);      // **


// ============================================================================
// COMPARISON OPERATIONS (CHUNGUS Coercion Rules)
// ============================================================================

// All comparisons promote both operands to number
// Result type: always TY_BOOL

ChValue ch_less(ChValue left, ChValue right);        // <
ChValue ch_greater(ChValue left, ChValue right);     // >
ChValue ch_le(ChValue left, ChValue right);          // <=
ChValue ch_ge(ChValue left, ChValue right);          // >=
ChValue ch_eq(ChValue left, ChValue right);          // ==
ChValue ch_ne(ChValue left, ChValue right);          // !=


// ============================================================================
// LOGICAL OPERATIONS (CHUNGUS Coercion Rules)
// ============================================================================

// All logical ops promote operands to bool
// Result type: always TY_BOOL

ChValue ch_and(ChValue left, ChValue right);   // &
ChValue ch_or(ChValue left, ChValue right);    // |
ChValue ch_not(ChValue operand);               // !


// ============================================================================
// ARRAY OPERATIONS
// ============================================================================

// Get element from 1D array
ChValue ch_array_get_1d(ChValue arr, int index);

// Set element in 1D array
void ch_array_set_1d(ChValue* arr, int index, ChValue value);

// Get element from 2D array
ChValue ch_array_get_2d(ChValue arr, int row, int col);

// Set element in 2D array
void ch_array_set_2d(ChValue* arr, int row, int col, ChValue value);


// ============================================================================
// I/O OPERATIONS
// ============================================================================

// Print value to stdout (for "show" statement)
void ch_print(ChValue v);

// Read input from stdin (for "read" expression)
// Dynamic typing:
//   - integer text -> TY_INT
//   - floating text -> TY_FLOAT
//   - otherwise -> TY_STRING
ChValue ch_read(void);


// ============================================================================
// MEMORY MANAGEMENT
// ============================================================================

// Deep copy a value (for assignment)
ChValue ch_copy(ChValue src);

// Free allocated memory (strings, arrays)
void ch_free(ChValue* v);


// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// Get type name as string (for debugging/errors)
const char* ch_type_name(ChType type);

// Print type and value (for debugging)
void ch_debug_print(ChValue v);

#endif // CHUNGUS_RUNTIME_H
