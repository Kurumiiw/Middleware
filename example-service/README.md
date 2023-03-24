# Example service

This example service shows how to integrate the middleware in a new python
project, with the middleware as a dependency. It does not implement any
functionality outside of the example given in the middleware readme.

It assumes that `poetry` is already installed on the system.

## Using path dependency

As an alternative to following the steps described here, one can also choose to copy this project
folder and use that as a starting point instead.

- Create a new directory for the project and navigate to it.

- Run `poetry init` and fill in the details. Skip the prompt to set up dependencies interactively.

- In the generated `pyproject.toml` file, add the following line to the
  `[tool.poetry.dependencies]` section ([See also](https://python-poetry.org/docs/dependency-specification/#path-dependencies)):

```
[tool.poetry.dependencies]
python = "^3.10"
middleware = { path = "/PATH/TO/MIDDLEWARE", develop = true }
```

- Run `poetry shell`, `poetry install` to create/activate a virtual environment
  and install packages.

- Copy the `example_service/main.py` file into the project and run it to
  confirm it is working.

## Using Github releases

We have not yet found a way for `poetry` to be configured to authenticate when using python releases, so for now setting up a git dependency referencing the appropriate tag is the easiest way to make this work.

A [git dependency](https://python-poetry.org/docs/dependency-specification/#git-dependencies) is specified by replacing the `middleware = ` line in the path dependencies
example with `{ git = ... }`. For instance:

```
[tool.poetry.dependencies]
python = "^3.10"
middleware = { git = "https://github.com/Kurumiiw/Middleware.git", tag = "v0.1.0", subdirectory="middleware" }
```

A list of releases is provided [here](https://github.com/Kurumiiw/Middleware/releases)
