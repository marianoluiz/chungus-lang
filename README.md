# Hue Language

A clean, minimal, sleek general programming language.

## Tech Stack
- Java, mvn, docker

## Architecture
- .hue -> .c -> machine lang

## Get Started
1. **Install Docker**

    Download and install docker from [the official site](https://docs.docker.com/engine/install/).

2. **Build and run the Image**

    a. **Run quickly**
    ```sh
    docker build -t hue .

    docker run --rm -it hue
    ```

    b. **Setup Vscode Task for easier re-build and runs**
    - Create .vscode folder in the project root directory
    - Create `task.json` inside the .vscode folder
    ```json
    {
      "version": "2.0.0",
      "tasks": [
        {
          "label": "docker-build-run",
          "dependsOn": ["docker-build", "docker-run"],
          "dependsOrder": "sequence",
          "problemMatcher": []
        },
        {
          "label": "docker-build",
          "type": "shell",
          "command": "docker build -t hue .",
          "problemMatcher": []
        },
        {
          "label": "docker-run",
          "type": "shell",
          "command": "docker run --rm -it hue",
          "problemMatcher": []
        }
      ]
    }
    ```
    - Click search bar in vscode then search `> Run Task` then select `docker-build-run`.

    - You can set up a vscode keyboard for the `Run Task` or the `docker-build-run` for easier re-build and run.

