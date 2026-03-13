# CHUNGUS Runtime Library

This directory contains the C runtime library for the CHUNGUS compiler.

## Overview

The CHUNGUS runtime implements a dynamic type system with tagged unions and CHUNGUS-specific type coercion rules. All CHUNGUS values are represented as `ChValue` structs that can hold:

- **int**: Integer values
- **float**: Floating-point values  
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

## API Reference

### Constructors
```c
ChValue ch_int(int x);
ChValue ch_float(double x);
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

`ch_read()` performs dynamic input typing:
- integer text → `TY_INT`
- floating text → `TY_FLOAT`
- non-numeric text (or empty after parse fallback) → `TY_STRING`

`ch_print()` flushes stdout after each print so output is visible for long-running loops.

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
- Division by zero detection
- Deep copying for assignment (no aliasing issues)

Runtime errors print helpful messages to stderr and return safe default values.

When codegen lowers `for ... in range(...)`, runtime behavior includes:
- support for 1/2/3 range arguments
- positive and negative step handling
- runtime guard for `step == 0` (prints error and skips loop)

## Performance Notes

- Value types (int, float, bool) are copied by value
- Strings and arrays are heap-allocated and reference-counted via manual copying
- Type checks happen at runtime for every operation
- For production use, consider adding JIT compilation or ahead-of-time optimizations based on semantic analysis type annotations
