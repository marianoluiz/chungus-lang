# CHUNGUS Runtime Library

This directory contains the C runtime library for the CHUNGUS compiler.

## Overview

The CHUNGUS runtime implements a dynamic type system with tagged unions and CHUNGUS-specific type coercion rules. All CHUNGUS values are represented as `ChValue` structs that can hold:

- **int**: 64-bit signed integer values (`int64_t`, range `[-9223372036854775808, 9223372036854775807]`)
- **float**: Floating-point values, normalized to at most 6 fractional decimal places
- **bool**: Boolean values
- **string**: String values (heap-allocated)
- **array**: 1D or 2D arrays of ChValue (heterogeneous, heap-allocated)

## Files

- **`chungus_runtime.h`** - Runtime library header with all function declarations
- **`chungus_runtime.c`** - Runtime library implementation
- **`test_runtime.c`** - Test suite demonstrating all runtime features
- **`Makefile`** - Build automation

## Type Coercion Rules

The runtime implements CHUNGUS type coercion exactly as specified:

### Numeric Promotion (`ch_to_number`)
Converts values for arithmetic/relational operations (returns `double` for computation):
- `int` → integer value
- `float` → float value
- `bool` → `true` = 1, `false` = 0 (integer values)
- `string` → non-empty = 1, empty = 0 (integer values)
- `array` → error (returns 0)

### Boolean Promotion (`ch_to_bool`)
Converts values to `bool` for logical operations:
- `bool` → identity
- `int` → non-zero = true, zero = false
- `float` → non-zero = true, zero = false
- `string` → non-empty = true, empty = false
- `array` → non-empty = true, empty = false

### Arithmetic Result Types
- `/` (division) **always** returns `TY_FLOAT`
- If either operand is `TY_FLOAT` → result is `TY_FLOAT`
- Otherwise (both int-like: `TY_INT`, `TY_BOOL`, `TY_STRING`) → result is `TY_INT`

## Numeric Limits

### Integer (`TY_INT`)
- Stored as `int64_t` (64-bit signed)
- Valid range: `[-9223372036854775808, 9223372036854775807]`
- Maximum input digits: **19**
- Negative notation (CHUNGUS style): `~N` (e.g. `~42`, `~9223372036854775807`)
- Arithmetic results that overflow the 64-bit range produce a runtime error and return `0`

### Float (`TY_FLOAT`)
- Stored as `double`, but normalized to at most **6 fractional decimal places**
- Trailing zeros after the decimal point are trimmed, but at least one digit is kept (e.g. `1.0`, `3.14`, `1.323321`)
- Negative notation (CHUNGUS style): `~N.NN` (e.g. `~3.14`)
- Input with more than 6 fractional digits produces a runtime error and returns `0.0`
- All float values are passed through `ch_round_to_6dp()` on construction

## API Reference

### Constructors
```c
ChValue ch_int(int64_t x);   // 64-bit signed integer
ChValue ch_float(double x);  // normalized to 6 fractional dp
ChValue ch_bool(bool x);
ChValue ch_str(const char* x);
ChValue ch_array_1d(size_t size);
ChValue ch_array_2d(size_t rows, size_t cols);
```

### Arithmetic Operations
All arithmetic operations promote operands to numbers:
```c
ChValue ch_add(ChValue left, ChValue right);   // +
ChValue ch_sub(ChValue left, ChValue right);   // -
ChValue ch_mul(ChValue left, ChValue right);   // *
ChValue ch_div(ChValue left, ChValue right);   // / (always float)
ChValue ch_idiv(ChValue left, ChValue right);  // // (integer division)
ChValue ch_mod(ChValue left, ChValue right);   // %
ChValue ch_pow(ChValue left, ChValue right);   // **
```

### Comparison Operations
All comparisons promote operands to numbers, return bool:
```c
ChValue ch_less(ChValue left, ChValue right);     // <
ChValue ch_greater(ChValue left, ChValue right);  // >
ChValue ch_le(ChValue left, ChValue right);       // <=
ChValue ch_ge(ChValue left, ChValue right);       // >=
ChValue ch_eq(ChValue left, ChValue right);       // ==
ChValue ch_ne(ChValue left, ChValue right);       // !=
```

### Logical Operations
All logical operations promote operands to bool, return bool:
```c
ChValue ch_and(ChValue left, ChValue right);  // &
ChValue ch_or(ChValue left, ChValue right);   // |
ChValue ch_not(ChValue operand);              // !
```

### Array Operations
```c
ChValue ch_array_get_1d(ChValue arr, int index);
void ch_array_set_1d(ChValue* arr, int index, ChValue value);
ChValue ch_array_get_2d(ChValue arr, int row, int col);
void ch_array_set_2d(ChValue* arr, int row, int col, ChValue value);
```

All array operations include bounds checking with runtime error messages.

### I/O Operations
```c
void ch_print(ChValue v);     // Print value (for "show" statement)
ChValue ch_read(void);        // Read line from stdin (for "read" expression)
```

#### `ch_read()` — Dynamic Input Typing
Reads one line from stdin and infers its type:
- Integer text (digits only, optional leading `-` or `~`) → `TY_INT`
- Decimal text (digits with `.`, optional leading `-` or `~`) → `TY_FLOAT`
- Any other text → `TY_STRING`

Input validation:
- Integer: max **19 digits**; must fit in signed 64-bit range
- Float: max **6 fractional digits**
- Both `~N` and `-N` are accepted as negative numeric input (CHUNGUS and C style)
- Exceeding any limit prints a runtime error and returns `0` / `0.0`

#### `ch_print()` — CHUNGUS Output Notation
- Integers: printed as `N` (positive) or `~N` (negative) — **no `-` sign**
- Floats: printed with up to 6 fractional digits, trailing zeros trimmed, minimum `.0` kept; negative shown as `~N.NN`
- Bools: `TRUE` or `FALSE`
- Strings: printed as-is
- Flushes stdout after each call (important for GUI/live output)

Examples:
| Value | Output |
|-------|--------|
| `ch_int(42)` | `42` |
| `ch_int(-7)` | `~7` |
| `ch_float(3.14)` | `3.14` |
| `ch_float(-1.5)` | `~1.5` |
| `ch_float(1.0)` | `1.0` |
| `ch_bool(true)` | `TRUE` |

### Memory Management
```c
ChValue ch_copy(ChValue src);  // Deep copy (handles strings/arrays)
void ch_free(ChValue* v);      // Free allocated memory
```

**Important**: Always call `ch_free` on strings and arrays before program exit to prevent memory leaks.

## Building

### Build runtime library
```bash
make
```

### Run tests
```bash
make test
```

### Compile a CHUNGUS-generated program
```bash
make run PROGRAM=output.c
```

### Clean build artifacts
```bash
make clean
```

## Example Usage

```c
#include "chungus_runtime.h"

int main() {
    // Variables
    ChValue x = ch_int(42);
    ChValue y = ch_int(10);
    
    // Arithmetic with type promotion
    ChValue result = ch_add(x, y);  // 52
    
    // Output
    ch_print(result);  // Prints: 52
    
    return 0;
}
```

Compile with:
```bash
gcc -o program program.c chungus_runtime.c -lm
```

## Code Generation Tips

When generating C code from CHUNGUS AST:

1. **Declare all variables as `ChValue`**:
   ```c
   ChValue x;
   ChValue y;
   ChValue result;
   ```

2. **Use constructors for literals**:
   ```c
   x = ch_int(42);
   y = ch_float(3.14);
   ```

3. **Use runtime functions for all operations**:
   ```c
   result = ch_add(x, y);
   ```

4. **Use `ch_to_bool` for conditions**:
   ```c
   if (ch_to_bool(condition)) {
       // ...
   }
   ```

5. **Always include the runtime header**:
   ```c
   #include "chungus_runtime.h"
   ```

## Memory Safety

The runtime provides:
- Bounds checking on all array accesses
- Null checks on string operations
- Division by zero and modulo by zero detection
- Overflow detection for all integer-producing arithmetic operations
- 64-bit range validation on `ch_read()` integer input
- Deep copying for assignment (no aliasing issues)

Runtime errors print helpful messages to stderr and return safe default values (typically `0`, `0.0`, or `""`).

When codegen lowers `for ... in range(...)`, runtime behavior includes:
- Support for 1/2/3 range arguments
- Positive and negative step handling
- Runtime guard for `step == 0` (prints error and skips loop)

## Performance Notes

- Value types (int, float, bool) are copied by value
- Strings and arrays are heap-allocated; use `ch_copy`/`ch_free` for ownership
