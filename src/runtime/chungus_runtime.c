/**
 * CHUNGUS Runtime Library - Implementation
 * 
 * Implements CHUNGUS type coercion rules and dynamic operations.
 */

#define _POSIX_C_SOURCE 200809L
#include "chungus_runtime.h"
#include <ctype.h>
#include <errno.h>
#include <limits.h>

// ============================================================================
// INPUT VALIDATION HELPERS
// ============================================================================

static int ch_count_digits(const char* s) {
    int count = 0;
    for (const char* p = s; *p; p++) {
        if (isdigit((unsigned char)*p)) {
            count++;
        }
    }
    return count;
}

static bool ch_is_integer_text(const char* s) {
    if (!s || *s == '\0') return false;

    const char* p = s;
    if (*p == '+' || *p == '-') p++;
    if (!isdigit((unsigned char)*p)) return false;

    while (*p) {
        if (!isdigit((unsigned char)*p)) return false;
        p++;
    }
    return true;
}

static bool ch_is_decimal_text(const char* s, int* frac_digits_out) {
    if (!s || *s == '\0') return false;

    const char* p = s;
    if (*p == '+' || *p == '-') p++;

    bool seen_dot = false;
    bool seen_digit = false;
    int frac_digits = 0;

    while (*p) {
        if (*p == '.') {
            if (seen_dot) return false;
            seen_dot = true;
            p++;
            continue;
        }

        if (!isdigit((unsigned char)*p)) {
            return false;
        }

        seen_digit = true;
        if (seen_dot) frac_digits++;
        p++;
    }

    if (frac_digits_out) *frac_digits_out = frac_digits;
    return seen_digit && seen_dot;
}

static double ch_round_to_6dp(double x) {
    return round(x * 1000000.0) / 1000000.0;
}

static bool ch_double_to_int64_checked(double x, int64_t* out) {
    if (!isfinite(x)) {
        fprintf(stderr, "Runtime Error: Numeric result is not finite\n");
        return false;
    }

    long double xl = (long double)x;
    if (xl < -9223372036854775808.0L || xl > 9223372036854775807.0L) {
        fprintf(stderr,
                "Runtime Error: Integer result out of signed 64-bit range [-9223372036854775808, 9223372036854775807]\n");
        return false;
    }

    *out = (int64_t)x;
    return true;
}


// ============================================================================
// CONSTRUCTORS
// ============================================================================

ChValue ch_int(int64_t x) {
    ChValue v;
    v.type = TY_INT;
    v.i = x;
    return v;
}

ChValue ch_float(double x) {
    ChValue v;
    v.type = TY_FLOAT;

    if (!isfinite(x)) {
        fprintf(stderr, "Runtime Error: Float value is not finite\n");
        v.f = 0.0;
    } else {
        v.f = ch_round_to_6dp(x);
    }

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

size_t ch_to_array_size_checked(ChValue v, const char* context) {
    const char* label = (context && *context) ? context : "array size";
    double x = ch_to_number(v);

    if (!isfinite(x)) {
        fprintf(stderr, "Runtime Error: %s must be a positive integer\n", label);
        exit(EXIT_FAILURE);
    }

    if (x != floor(x)) {
        fprintf(stderr, "Runtime Error: %s must be a positive integer\n", label);
        exit(EXIT_FAILURE);
    }

    long double xl = (long double)x;
    if (xl < 1.0L || xl > (long double)SIZE_MAX) {
        fprintf(stderr, "Runtime Error: %s out of valid range\n", label);
        exit(EXIT_FAILURE);
    }

    return (size_t)x;
}

int ch_to_index_checked(ChValue v, const char* context) {
    const char* label = (context && *context) ? context : "array index";
    double x = ch_to_number(v);

    if (!isfinite(x)) {
        fprintf(stderr, "Runtime Error: %s must be a non-negative integer\n", label);
        exit(EXIT_FAILURE);
    }

    if (x != floor(x)) {
        fprintf(stderr, "Runtime Error: %s must be a non-negative integer\n", label);
        exit(EXIT_FAILURE);
    }

    long double xl = (long double)x;
    if (xl < 0.0L || xl > (long double)INT_MAX) {
        fprintf(stderr, "Runtime Error: %s out of valid range\n", label);
        exit(EXIT_FAILURE);
    }

    return (int)x;
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

    int64_t ires = 0;
    if (!ch_double_to_int64_checked(result, &ires)) {
        return ch_int(0);
    }
    return ch_int(ires);
}

ChValue ch_sub(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = l - r;
    
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }

    int64_t ires = 0;
    if (!ch_double_to_int64_checked(result, &ires)) {
        return ch_int(0);
    }
    return ch_int(ires);
}

ChValue ch_mul(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = l * r;
    
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }

    int64_t ires = 0;
    if (!ch_double_to_int64_checked(result, &ires)) {
        return ch_int(0);
    }
    return ch_int(ires);
}

ChValue ch_div(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);

    if (r == 0.0) {
        fprintf(stderr, "Runtime Error: Division by zero\n");
        return ch_float(0.0);
    }
    
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
    
    double result = l / r;
    int64_t ires = 0;
    if (!ch_double_to_int64_checked(result, &ires)) {
        return ch_int(0);
    }
    return ch_int(ires);
}

ChValue ch_mod(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    
    if (r == 0.0) {
        fprintf(stderr, "Runtime Error: Modulo by zero\n");
        return ch_int(0);
    }
    
    int64_t li = 0;
    int64_t ri = 0;

    if (!ch_double_to_int64_checked(l, &li) || !ch_double_to_int64_checked(r, &ri)) {
        return ch_int(0);
    }

    if (ri == 0) {
        fprintf(stderr, "Runtime Error: Modulo by zero\n");
        return ch_int(0);
    }

    return ch_int(li % ri);
}

ChValue ch_pow(ChValue left, ChValue right) {
    double l = ch_to_number(left);
    double r = ch_to_number(right);
    double result = pow(l, r);
    
    if (left.type == TY_FLOAT || right.type == TY_FLOAT) {
        return ch_float(result);
    }

    int64_t ires = 0;
    if (!ch_double_to_int64_checked(result, &ires)) {
        return ch_int(0);
    }
    return ch_int(ires);
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

static void ch_print_float_6dp(double value) {
    bool is_neg = value < 0.0;
    if (is_neg) {
        value = -value;
    }

    // Print with fixed 6 decimal places, then trim trailing zeros,
    // but keep at least one fractional digit so float stays visibly float.
    char buf[64];
    snprintf(buf, sizeof(buf), "%.6f", value);

    char* dot = strchr(buf, '.');
    if (!dot) {
        printf("%s", buf);
        return;
    }

    char* end = buf + strlen(buf) - 1;
    while (end > dot && *end == '0') {
        *end-- = '\0';
    }
    if (end == dot) {
        *(++end) = '0';
        *(++end) = '\0';
    }

    if (is_neg) {
        printf("~%s", buf);
    } else {
        printf("%s", buf);
    }
}

void ch_print(ChValue v) {
    switch (v.type) {
        case TY_INT:
            if (v.i < 0) {
                // Print CHUNGUS negative style (~N) while safely handling INT64_MIN
                uint64_t mag = (uint64_t)(-(v.i + 1)) + 1;
                printf("~%llu", (unsigned long long)mag);
            } else {
                printf("%lld", (long long)v.i);
            }
            break;
        
        case TY_FLOAT:
            ch_print_float_6dp(v.f);
            break;
        
        case TY_BOOL:
            printf("%s", v.b ? "true" : "false");
            break;
        
        case TY_STRING:
            printf("%s", v.s);
            break;
        
        case TY_ARRAY:
            printf("[Array %zux%zu]", v.arr.rows, v.arr.cols);
            break;
    }

    // Important for GUI/live execution: force buffered output to appear
    // even if the program is long-running or stuck in an infinite loop.
    fflush(stdout);
}

ChValue ch_read(void) {
    char buffer[1024];

    if (fgets(buffer, sizeof(buffer), stdin) != NULL) {
        // Remove trailing newline
        size_t len = strlen(buffer);
        if (len > 0 && buffer[len - 1] == '\n') {
            buffer[len - 1] = '\0';
        }

        // Trim leading/trailing whitespace for numeric parsing
        char* start = buffer;
        while (*start && isspace((unsigned char)*start)) {
            start++;
        }

        char* end = start + strlen(start);
        while (end > start && isspace((unsigned char)end[-1])) {
            end--;
        }
        *end = '\0';

        // Empty input -> empty string
        if (*start == '\0') {
            return ch_str("");
        }

        // CHUNGUS negative style support for input parsing:
        // ~123 and ~1.25 are treated as -123 and -1.25 for numeric reads.
        const char* parse_text = start;
        char normalized[1024];
        if (start[0] == '~') {
            normalized[0] = '-';
            strncpy(normalized + 1, start + 1, sizeof(normalized) - 2);
            normalized[sizeof(normalized) - 1] = '\0';
            parse_text = normalized;
        }

        // Integer input: max 19 digits
        if (ch_is_integer_text(parse_text)) {
            int digit_count = ch_count_digits(parse_text);
            if (digit_count > 19) {
                fprintf(stderr, "Runtime Error: Integer input exceeds 19-digit limit: '%s'\n", start);
                return ch_int(0);
            }

            errno = 0;
            char* int_end = NULL;
            long long int_val = strtoll(parse_text, &int_end, 10);
            if (errno == ERANGE) {
                fprintf(stderr,
                        "Runtime Error: Integer input out of signed 64-bit range [-9223372036854775808, 9223372036854775807]: '%s'\n",
                        start);
                return ch_int(0);
            }

            if (int_end == parse_text || *int_end != '\0') {
                fprintf(stderr, "Runtime Error: Invalid integer input: '%s'\n", start);
                return ch_int(0);
            }

            return ch_int((int64_t)int_val);
        }

        // Decimal input: max 6 fractional digits
        int frac_digits = 0;
        if (ch_is_decimal_text(parse_text, &frac_digits)) {
            if (frac_digits > 6) {
                fprintf(stderr, "Runtime Error: Decimal input exceeds 6 fractional digits: '%s'\n", start);
                return ch_float(0.0);
            }

            errno = 0;
            char* float_end = NULL;
            double float_val = strtod(parse_text, &float_end);
            if (errno != 0 || float_end == parse_text || *float_end != '\0') {
                fprintf(stderr, "Runtime Error: Invalid decimal input: '%s'\n", start);
                return ch_float(0.0);
            }

            return ch_float(float_val);
        }

        // Fallback: string
        return ch_str(start);
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
