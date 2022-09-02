FROM python:3.10 as development

ARG NODE_ENV=development
ENV NODE_ENV=${NODE_ENV}

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

CMD ["gunicorn"  , "--timeout", "1000", "--workers", "1", "--threads", "4", "--log-level", "debug", "--bind", "0.0.0.0:5001", "app:app"]

FROM python:3.10 as production

ARG NODE_ENV=production
ENV NODE_ENV=${NODE_ENV}

COPY ./requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

CMD ["gunicorn"  , "--timeout", "1000", "--workers", "1", "--threads", "4", "--log-level", "debug", "--bind", "0.0.0.0:${PORT}", "app:app"]