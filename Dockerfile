# syntax=docker/dockerfile:1

FROM python:3.10

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 8080

CMD ["gunicorn"  , "-b", "0.0.0.0:8080", "app:app"]