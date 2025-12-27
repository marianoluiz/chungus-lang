# How to build & run?
```
docker build -t chg-compiler .
docker run --rm -it chg-compiler /bin/sh
docker run --rm -it chg-compiler python -m src.lexer
docker run --rm -it chg-compiler python -m src.syntax
```

### --rm
- Automatically removes the container after it exits.
- Keeps your system clean so old containers don’t pile up.

### -it
- -i → interactive mode (keeps STDIN open).
- -t → allocates a terminal so you can see output and type input.
- Together, -it makes the container act like a normal program in your terminal.


- Every time you change source code, Docker does not reinstall dependencies, because pip install is cached