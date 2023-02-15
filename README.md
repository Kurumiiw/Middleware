# Middleware

## Building and running docker image

Do the following while in the subfolder `middleware/`

- `docker build -t middleware .`
- `docker run -it middleware`

For macOS on Apple Silicon, you need to target the right architecture:

- `docker build --platform linux/amd64 -t middleware  .`
- `docker run -it --platform linux/amd64 middleware`

## Poetry

Do the following while in the subfolder `middleware/`

- To install dependencies: `poetry install`
- To activate virtual environment: `poetry shell`
- To add dependencies: `poetry add [-D] X` (Use -D for development dependencies)
