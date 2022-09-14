# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ARG FCM_TOKEN

ENV FCM_TOKEN = ${FCM_TOKEN} \
    MONGO_URI = ${MONGO_URI} \
    REDIS_URL = ${REDIS_URL} \
    ENV_MODE = ${ENV_MODE} \
    FERNET_KEY = ${FERNET_KEY} \
    JWT_TOKEN = ${JWT_TOKEN}

CMD ["honcho", "start"]