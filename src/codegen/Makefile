# Makefile for CHUNGUS Runtime Library

CC = gcc 							# Which compiler to use
# CFLAGS = -Wall -Wextra -std=c99 -Wno-unused-variable # Compiler flags (-Wall = show all warnings)
CFLAGS = -w -std=c99
LDFLAGS = -lm						# Linker flags (-lm = link math library)

# Runtime library files
RUNTIME_H = chungus_runtime.h
RUNTIME_C = chungus_runtime.c
RUNTIME_O = chungus_runtime.o

# Test program
TEST_C = test_runtime.c
TEST_BIN = test_runtime

.PHONY: all test clean

all: $(RUNTIME_O)					# Default target when you just type 'make'

# Compile runtime library to object file
$(RUNTIME_O): $(RUNTIME_C) $(RUNTIME_H)
	$(CC) $(CFLAGS) -c $(RUNTIME_C) -o $(RUNTIME_O)

# Build and run test program
test: $(TEST_BIN)           		# Type 'make test' to run this
	./$(TEST_BIN)

$(TEST_BIN): $(TEST_C) $(RUNTIME_C) $(RUNTIME_H)
	$(CC) $(CFLAGS) -o $(TEST_BIN) $(TEST_C) $(RUNTIME_C) $(LDFLAGS)

# Clean build artifacts
clean:	                      		# Type 'make clean'
	rm -f $(RUNTIME_O) $(TEST_BIN)

# Compile a CHUNGUS-generated C file
# Usage: make run PROGRAM=output.c
run: $(RUNTIME_O)         			# Type 'make run PROGRAM=mycode.c'
	$(CC) $(CFLAGS) -o program $(PROGRAM) $(RUNTIME_C) $(LDFLAGS)
	./program
