# syntax=docker/dockerfile:1

FROM python:3.10-slim-buster

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ARG FCM_TOKEN=${FCM_TOKEN}
ARG MONGO_URI=${MONGO_URI}
ARG REDIS_URL=${REDIS_URL}
ARG ENV_MODE=${REDIS_URL}
ARG FERNET_KEY=${FERNET_KEY}
ARG JWT_TOKEN=${JWT_TOKEN}

ENV FCM_TOKEN ${FCM_TOKEN} 
ENV MONGO_URI ${MONGO_URI} 
ENV REDIS_URL ${REDIS_URL} 
ENV ENV_MODE ${ENV_MODE} 
ENV FERNET_KEY ${FERNET_KEY} 
ENV JWT_TOKEN ${JWT_TOKEN}

CMD ["honcho", "start"]