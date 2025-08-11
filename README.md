# Hue Language

A clean, minimal, sleek, general programming language.

## Tech Stack
- Java, mvn, docker

## Architecture
- .hue -> .c -> machine lang

## Steps
  1. *Parsing* is taking raw code and turning it into a more abstract
    representation of the code. Lexical & Syntetic Analysis.
  2. *Transformation* takes this abstract representation and manipulates to do
    whatever the compiler wants it to.
  3. *Code Generation* takes the transformed representation of the code and
    turns it into new code.

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


    b. **Use vscode Remote Window** (Recommended)

      See [official docs and reference of vscode Dev Containers](https://code.visualstudio.com/docs/devcontainers/containers).

      - Install extension

        ![Remote Window Button](/docs/1.docker-ext.png)
        <br><br>
      

      - Click the `Remote Window Button`

        ![Remote Window Button](/docs/2.remote-window.png)
        <br><br>

      - Click the `reopen in container`

        ![Remote Window Button](/docs/3.reopen-container.png)
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
            - create the pre-launch task script or `task.json` for to automate building the container

                ```json
                {
                  "version": "2.0.0",
                  "tasks": [
                    {
                      "label": "build",
                      "type": "shell",
                      "command": "mvn compile && echo Build Successful",
                      "problemMatcher": []
                    },
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
            <br><br>

      - Click `run and debug` to build and run.
      ![Run and Debug](/docs/4.run-debug.png)
      <br><br>

3. How to use GitHub to contribute?

    - Make sure you have GitHub

    - If in dev container environment, Click `remote container button ` then Click `re-open in local environment`
    
    - Make sure to Create git branch before any changes
    
    - git add, commit, push to your branch
