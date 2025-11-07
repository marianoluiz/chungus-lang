# CHUNGUS Language
A clean, minimal, general programming language.

## Tech Stack
- Python

## Get Started
1. Create a virtual environment. For CMD or PowerShell, run `python -m venv .venv`. For Bash, run `python3 -m venv .venv`.
2. Activate the virtual environment. For CMD, run `.venv\Scripts\activate`. For PowerShell, run `.venv\Scripts\Activate.ps1`. For Bash, run `source .venv/bin/activate`. You can also use venv.

## Planned Architecture
```
chungus-lang/                          # project root (/mnt/drive_d/projs/compiler/chungus-lang)
├── README.md
├── pyproject.toml
├── LICENSE
├── docs/                               # design notes, DFA diagrams, API docs
│   └── dfa.md
├── examples/                           # example source programs
│   └── hello.chg
├── scripts/                            # helper scripts (run, build, visualize)
│   └── run_gui.sh
├── src/
│   └── chungus/
│       ├── __init__.py
│       ├── cli.py                      # small CLI wrapper (uses services)
│       ├── gui.py                      # Tkinter GUI (calls services, no lexer logic)
│       ├── token.py                    # Token dataclass + TokenType enum
│       ├── dfa.py                      # State, Transition, InputCategory, helpers
│       ├── trace.py                    # StateTraceEntry dataclass, trace utilities
│       ├── utils.py                    # small helpers (positioning, categorization)
│       ├── services/
│       │   ├── __init__.py
│       │   ├── lexer_service.py        # analyze_with_trace API -> (tokens, errors, trace)
│       │   └── pipeline_service.py     # orchestrate lexer->parser->semantic for GUI/CLI
│       ├── lexer/                      # lexer subsystem (pure, no UI)
│       │   ├── __init__.py
│       │   ├── core.py                 # LexerRunner: drives DFA, emits tokens & trace
│       │   ├── rules.py                # tokenization rules, categories, delim definitions
│       │   └── errors.py               # lexical error types
│       ├── parser/                     # syntactic analyzer
│       │   ├── __init__.py
│       │   ├── core.py                 # parser driver (recursive descent / table-driven)
│       │   ├── grammar.py              # grammar definitions / productions
│       │   ├── ast.py                  # AST node classes & builders
│       │   └── errors.py               # syntactic error reporting
│       ├── semantic/                   # semantic analyzer & symbol table
│       │   ├── __init__.py
│       │   ├── analyzer.py             # type checking, scope checks, inference
│       │   ├── symbol_table.py
│       │   └── types.py
│       ├── ir/                         # optional intermediate representation
│       │   ├── __init__.py
│       │   ├── nodes.py
│       │   └── builder.py
│       └── runtime/                    # interpreter / VM and standard library
│           ├── __init__.py
│           ├── vm.py
│           └── stdlib.py
├── tests/                              # unit/integration tests
│   ├── test_lexer.py
│   ├── test_trace.py
│   ├── test_parser.py
│   └── test_semantic.py
├── tools/                              # dev tools: visualize DFA, generate diagrams
│   └── visualize_dfa.py
└── .gitignore
```

## Setup Docker Instruction
1. **Install Docker**

    Download and install docker from [the official site](https://docs.docker.com/engine/install/).

2. **Build and run the Image**

    Ways to run: 

    a. **Run quickly**
      ```sh
      docker build -t hue .

      docker run --rm -it hue
      ```


    b. **Use vscode Remote Window** (Recommended)

      See [official docs and reference of vscode Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers).

      - Install extension

        ![Remote Window Button](/md_files/1.docker-ext.png)
        <br><br>
      

      - Click the `Remote Window Button`

        ![Remote Window Button](/md_files/2.remote-window.png)
        <br><br>

      - Click the `reopen in container`

        ![Remote Window Button](/md_files/3.reopen-container.png)
        <br><br>

      - Configure the `.devcontainer` based on existing dockerfile

      - Add this in `.devcontainer` for proper linting and intellisense
        ```json
        {
          "name": "Existing Dockerfile",
          "build": {
            "context": "..",
            "dockerfile": "../Dockerfile"
          },
          "customizations": {
            "vscode": {
              "settings": {},
              "extensions": [
                "vscjava.vscode-java-pack"
              ]
            }
          }
        }
        ```
        <br><br>
      
      - Create a `launch script` and `task script`
          - You can click the run and debug and have a template launch script for java or create manually a `.vscode` folder then create `launch.json` file inside.

            ```json
            {
              "version": "0.2.0",
              "configurations": [
                {
                  "type": "java",
                  "name": "Launch with Arguments Prompt",
                  "request": "launch",
                  "mainClass": "dev.marianoluiz.Main",
                  "args": "${command:SpecifyProgramArgs}",
                  "preLaunchTask": "build",
                },
                {
                  "type": "java",
                  "name": "Launch",
                  "request": "launch",
                  "mainClass": "dev.marianoluiz.Main",
                  "projectName": "hue",
                  "preLaunchTask": "build",
                }
              ]
            }
            ```
              <br><br>
          - create the pre-launch task script or `task.json` to automate building the container

              ```json
              {
                "version": "2.0.0",
                "tasks": [
                  {
                    "label": "build",
                    "type": "shell",
                    "command": "mvn compile && echo Build Successful",
                    "problemMatcher": []
                  }
                ]
              }
              ```
          <br><br>

      - Click `run and debug` to build and run.

        ![Run and Debug](/md_files/4.run-debug.png)
        <br><br>

3. How to use GitHub to contribute?

    - Make sure you have GitHub

    - If in dev container environment, Click `remote container button ` then Click `re-open in local environment`
    
    - Make sure to Create git branch before any changes
    
    - git add, commit, push to your branch
