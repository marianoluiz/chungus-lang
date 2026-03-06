# HOW TO USE MAKEFILE

## Build just the runtime
make

## Build and test runtime
make test

## Clean up compiled files
make clean

## Run your generated code
make run PROGRAM=output.c


# check leak
valgrind --leak-check=full ./program