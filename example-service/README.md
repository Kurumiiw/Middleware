# Readme

This example service shows how to integrate the middleware in a new python
project, with the middleware as a dependency. It does not implement any
functionality outside of the example given in the project. This example
assumes that the middleware is located locally on the computer for now.

It assumes that `poetry` is already installed on the system.

TODO: Showcase example with prepackaged release.

## Steps

- Create a new directory for the project.

- Run `poetry init` and fill in the details. When prompted to configure
  dependencies interactively, don't.

- In the generated `pyproject.tom` file, add the following line to the
  `[tool.poetry.dependencies]` section ([See also](https://python-poetry.org/docs/dependency-specification/#path-dependencies)):

```
middleware = { path = "/PATH/TO/MIDDLEWARE", develop = true }
```

- Run `poetry shell`, `poetry install` to create/activate a virtual environment
  and install packages.

- Copy the `example_service/main.py` file into the project and run it to
  confirm it is working. (Note: at the time of writing this would _not_ work due
  to missing configuration file).
