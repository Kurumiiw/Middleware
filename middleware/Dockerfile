FROM python:3.10-alpine3.16

EXPOSE 5000

RUN pip install poetry

WORKDIR /app

COPY poetry.lock pyproject.toml .

RUN poetry config virtualenvs.create false \
    && poetry install

COPY ./middleware /app

CMD [ "python", "./test.py"]
