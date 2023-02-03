FROM python:3.10-alpine3.16

RUN pip install poetry

WORKDIR /app

COPY poetry.lock pyproject.toml .

RUN poetry config virtualenvs.create false \
 && poetry install

COPY ./middleware /app
RUN python test.py