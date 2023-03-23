# Example service

This example service shows how to integrate the middleware in a new python
project, with the middleware as a dependency. It does not implement any
functionality outside of the example given in the middleware readme.

It assumes that `poetry` is already installed on the system.

## Steps

As an alternative to the steps below, one can also choose to copy this project
folder and use that as a starting point instead.

- Create a new directory for the project.

- Run `poetry init` and fill in the details. When prompted to configure
  dependencies interactively, don't.

- In the generated `pyproject.toml` file, add the following line to the
  `[tool.poetry.dependencies]` section ([See also](https://python-poetry.org/docs/dependency-specification/#path-dependencies)):

```
middleware = { path = "/PATH/TO/MIDDLEWARE", develop = true }
```

- Run `poetry shell`, `poetry install` to create/activate a virtual environment
  and install packages.

- Copy the `example_service/main.py` file into the project and run it to
  confirm it is working.

## Using Github releases

Alternatively the dependency can be specified directly to a release on Github.
A [url dependency](https://python-poetry.org/docs/dependency-specification/#url-dependencies) is specified by replacing the `middleware = ` line in the above
example with `{ url = ... }`. For instance:

```
middleware = { url = "https://github.com/Kurumiiw/Middleware/releases/download/v0.1.0RC1/middleware-0.1.0.tar.gz" }
```

A list of releases is provided [here](https://github.com/Kurumiiw/Middleware/releases)
