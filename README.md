# Hue Language

A clean, minimal, sleek, general programming language.

## Tech Stack
- Java, mvn, docker

## Architecture
- .hue -> .c -> machine lang

## Get Started
1. **Install Docker**

    Download and install docker from [the official site](https://docs.docker.com/engine/install/).

2. **Build and run the Image**

    Ways to run: 

    a. **Run quickly**
      ```sh
      docker build -t hue .

      docker run --rm -it hue
      ```

    b. **Setup Vscode Task for easier re-build and runs** [This is one way to run it, but the linting and intellisense depend on the local version of your program which is not ideal.]
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

    c. **Open Project in Container** (Recommended)

      See [official docs and reference of vscode Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers).

      - Install extension
      ![Remote Window Button](/docs/1.docker-ext.png)

      - Click the `Remote Window Button`
      ![Remote Window Button](/docs/2.remote-window.png)
      
      - Click the `reopen container`
      ![Remote Window Button](/docs/3.reopen-container.png)

      - Configure the `.devcontainer` based on existing dockerfile

      - Add this in `.devcontainer` for proper linting and intellisense
      ```json
      "customizations": {
        "vscode": {
          "settings": {},
          "extensions": [
            "vscjava.vscode-java-pack"
          ]
        }}
      ```
      
      - Click `run and debug`, make sure you already have a launch.json for launching java maven projects. See .vscode if existing
      ![Run and Debug](/docs/4.run-debug.png)

3. How to use GitHub to contribute?

    - Make sure you have GitHub

    - If in dev container environment, Click `remote container button ` then Click `re-open in local environment`
    
    - Make sure to Create git branch before any changes
    
    - git add, commit, push to your branch
