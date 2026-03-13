/**
 * CHUNGUS Runtime Library - Implementation
 * 
 * Implements CHUNGUS type coercion rules and dynamic operations.
 */

#define _POSIX_C_SOURCE 200809L
#include "chungus_runtime.h"


// ============================================================================
// CONSTRUCTORS
// ============================================================================

ChValue ch_int(int x) {
    ChValue v;
    v.type = TY_INT;
    v.i = x;
    return v;
}

ChValue ch_float(double x) {
    ChValue v;
    v.type = TY_FLOAT;
    v.f = x;
    return v;
}

ChValue ch_bool(bool x) {
    ChValue v;
    v.type = TY_BOOL;
    v.b = x;
    return v;
}

ChValue ch_str(const char* x) {
    ChValue v;
    v.type = TY_STRING;
    v.s = strdup(x ? x : "");
    return v;
}

ChValue ch_array_1d(size_t size) {
    ChValue v;
    v.type = TY_ARRAY;
    v.arr.len = size;
    v.arr.rows = 1;
    v.arr.cols = size;
    v.arr.items = malloc(sizeof(ChValue) * size);
    
    // Initialize all elements to int 0
    for (size_t i = 0; i < size; i++) {
        v.arr.items[i] = ch_int(0);
    }
    
    return v;
}

ChValue ch_array_2d(size_t rows, size_t cols) {
    ChValue v;
    v.type = TY_ARRAY;
    v.arr.len = rows * cols;
    v.arr.rows = rows;
    v.arr.cols = cols;
    v.arr.items = malloc(sizeof(ChValue) * rows * cols);
    
    // Initialize all elements to int 0
    for (size_t i = 0; i < rows * cols; i++) {
        v.arr.items[i] = ch_int(0);
    }
    
    return v;
}


// ============================================================================
// TYPE PROMOTION (CHUNGUS Coercion Rules)
// ============================================================================

double ch_to_number(ChValue v) {
    switch (v.type) {
        case TY_INT:
            return (double)v.i;
        
        case TY_FLOAT:
            return v.f;
        
        case TY_BOOL:
            // true→1, false→0 (integer values)
            return v.b ? 1.0 : 0.0;
        
        case TY_STRING:
            // Non-empty→1, empty→0 (integer values)
            return (v.s && strlen(v.s) > 0) ? 1.0 : 0.0;

        case TY_ARRAY:
            // Arrays cannot be coerced to number
            fprintf(stderr, "Runtime Error: Cannot coerce array to number\n");
            return 0.0;
    }
    
    return 0.0;
}

bool ch_to_bool(ChValue v) {
    switch (v.type) {
        case TY_BOOL:
            return v.b;
        
        case TY_INT:
            return v.i != 0;
        
        case TY_FLOAT:
            return v.f != 0.0;
        
        case TY_STRING:
            return v.s && strlen(v.s) > 0;
        
        case TY_ARRAY:
            return v.arr.len > 0;
    }
    
    return false;
}

bool ch_is_int_valued(ChValue v) {
    if (v.type == TY_INT) return true;
    if (v.type == TY_BOOL) return true;
    if (v.type == TY_FLOAT) {
        return v.f == floor(v.f);
    }
    return false;
}


// ============================================================================
// ARITHMETIC OPERATIONS (CHUNGUS Coercion Rules)
// ============================================================================

ChValue ch_add(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = l + r;
    
    // Result is float if either operand is float
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }
    
    return ch_int((int)result);
}

ChValue ch_sub(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = l - r;
    
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }
    
    return ch_int((int)result);
}

ChValue ch_mul(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = l * r;
    
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }
    
    return ch_int((int)result);
}

ChValue ch_div(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    
    // Division always returns float in CHUNGUS
    return ch_float(l / r);
}

ChValue ch_idiv(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    
    // Integer division
    if (r == 0.0) {
        fprintf(stderr, "Runtime Error: Division by zero\n");
        return ch_int(0);
    }
    
    return ch_int((int)(l / r));
}

ChValue ch_mod(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    
    if (r == 0.0) {
        fprintf(stderr, "Runtime Error: Modulo by zero\n");
        return ch_int(0);
    }
    
    return ch_int((int)l % (int)r);
}

ChValue ch_pow(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = pow(l, r);
    
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }
    
    return ch_int((int)result);
}


// ============================================================================
// COMPARISON OPERATIONS (CHUNGUS Coercion Rules)
// ============================================================================

ChValue ch_less(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    return ch_bool(l < r);
}

ChValue ch_greater(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    return ch_bool(l > r);
}

ChValue ch_le(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    return ch_bool(l <= r);
}

ChValue ch_ge(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    return ch_bool(l >= r);
}

ChValue ch_eq(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    return ch_bool(l == r);
}

ChValue ch_ne(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    return ch_bool(l != r);
}


// ============================================================================
// LOGICAL OPERATIONS (CHUNGUS Coercion Rules)
// ============================================================================

ChValue ch_and(ChValue left, ChValue right) {
    bool l = ch_to_bool(left);
    bool r = ch_to_bool(right);
    return ch_bool(l && r);
}

ChValue ch_or(ChValue left, ChValue right) {
    bool l = ch_to_bool(left);
    bool r = ch_to_bool(right);
    return ch_bool(l || r);
}

ChValue ch_not(ChValue operand) {
    return ch_bool(!ch_to_bool(operand));
}


// ============================================================================
// ARRAY OPERATIONS
// ============================================================================

ChValue ch_array_get_1d(ChValue arr, int index) {
    if (arr.type != TY_ARRAY) {
        fprintf(stderr, "Runtime Error: Cannot index non-array type\n");
        return ch_int(0);
    }
    
    // Bounds checking
    if (index < 0 || (size_t)index >= arr.arr.cols) {
        fprintf(stderr, "Runtime Error: Array index %d out of bounds [0, %zu)\n", 
                index, arr.arr.cols);
        return ch_int(0);
    }
    
    return ch_copy(arr.arr.items[index]);
}

void ch_array_set_1d(ChValue* arr, int index, ChValue value) {
    if (arr->type != TY_ARRAY) {
        fprintf(stderr, "Runtime Error: Cannot index non-array type\n");
        return;
    }
    
    // Bounds checking
    if (index < 0 || (size_t)index >= arr->arr.cols) {
        fprintf(stderr, "Runtime Error: Array index %d out of bounds [0, %zu)\n", 
                index, arr->arr.cols);
        return;
    }
    
    // Free old value and copy new one
    ch_free(&arr->arr.items[index]);
    arr->arr.items[index] = ch_copy(value);
}

ChValue ch_array_get_2d(ChValue arr, int row, int col) {
    if (arr.type != TY_ARRAY) {
        fprintf(stderr, "Runtime Error: Cannot index non-array type\n");
        return ch_int(0);
    }
    
    // Bounds checking
    if (row < 0 || (size_t)row >= arr.arr.rows) {
        fprintf(stderr, "Runtime Error: Row index %d out of bounds [0, %zu)\n", 
                row, arr.arr.rows);
        return ch_int(0);
    }
    
    if (col < 0 || (size_t)col >= arr.arr.cols) {
        fprintf(stderr, "Runtime Error: Column index %d out of bounds [0, %zu)\n", 
                col, arr.arr.cols);
        return ch_int(0);
    }
    
    size_t index = row * arr.arr.cols + col;
    return ch_copy(arr.arr.items[index]);
}

void ch_array_set_2d(ChValue* arr, int row, int col, ChValue value) {
    if (arr->type != TY_ARRAY) {
        fprintf(stderr, "Runtime Error: Cannot index non-array type\n");
        return;
    }
    
    // Bounds checking
    if (row < 0 || (size_t)row >= arr->arr.rows) {
        fprintf(stderr, "Runtime Error: Row index %d out of bounds [0, %zu)\n", 
                row, arr->arr.rows);
        return;
    }
    
    if (col < 0 || (size_t)col >= arr->arr.cols) {
        fprintf(stderr, "Runtime Error: Column index %d out of bounds [0, %zu)\n", 
                col, arr->arr.cols);
        return;
    }
    
    size_t index = row * arr->arr.cols + col;
    
    // Free old value and copy new one
    ch_free(&arr->arr.items[index]);
    arr->arr.items[index] = ch_copy(value);
}


// ============================================================================
// I/O OPERATIONS
// ============================================================================

void ch_print(ChValue v) {
    switch (v.type) {
        case TY_INT:
            printf("%d", v.i);
            break;
        
        case TY_FLOAT:
            printf("%g", v.f);  // %g removes trailing zeros
            break;
        
        case TY_BOOL:
            printf("%s", v.b ? "TRUE" : "FALSE");
            break;
        
        case TY_STRING:
            printf("%s", v.s);
            break;
        
        case TY_ARRAY:
            printf("[Array %zux%zu]", v.arr.rows, v.arr.cols);
            break;
    }
}

ChValue ch_read(void) {
    char buffer[1024];
    if (fgets(buffer, sizeof(buffer), stdin) != NULL) {
        // Remove trailing newline
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') {
            buffer[len - 1] = '\0';
        }
        return ch_str(buffer);
    }
    return ch_str("");
}


// ============================================================================
// MEMORY MANAGEMENT
// ============================================================================

ChValue ch_copy(ChValue src) {
    if (src.type == TY_STRING) {
        return ch_str(src.s);  // strdup inside
    }
    
    if (src.type == TY_ARRAY) {
        // Deep copy array
        ChValue copy;
        copy.type = TY_ARRAY;
        copy.arr.len = src.arr.len;
        copy.arr.rows = src.arr.rows;
        copy.arr.cols = src.arr.cols;
        copy.arr.items = malloc(sizeof(ChValue) * src.arr.len);
        
        for (size_t i = 0; i < src.arr.len; i++) {
            copy.arr.items[i] = ch_copy(src.arr.items[i]);
        }
        
        return copy;
    }
    
    // int, float, bool are value types - shallow copy is fine
    return src;
}

void ch_free(ChValue* v) {
    if (v->type == TY_STRING) {
        free(v->s);
        v->s = NULL;
    }
    else if (v->type == TY_ARRAY) {
        // Recursively free all elements
        for (size_t i = 0; i < v->arr.len; i++) {
            ch_free(&v->arr.items[i]);
        }
        free(v->arr.items);
        v->arr.items = NULL;
    }
    
    v->type = TY_INT;  // Reset to safe default
}


// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

const char* ch_type_name(ChType type) {
    switch (type) {
        case TY_INT:    return "int";
        case TY_FLOAT:  return "float";
        case TY_BOOL:   return "bool";
        case TY_STRING: return "string";
        case TY_ARRAY:  return "array";
    }
    return "unknown";
}

void ch_debug_print(ChValue v) {
    printf("[%s] ", ch_type_name(v.type));
    ch_print(v);
    printf("\n");
}
