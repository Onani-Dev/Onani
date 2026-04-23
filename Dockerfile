# Multi-mode Flask app: development or production
# Runs in dev mode (Flask debug) by default
# Set FLASK_ENV=production to run Gunicorn + Caddy

FROM python:3.10-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev \
    && apk add libffi-dev

RUN apk add --no-cache ffmpeg

COPY requirements.txt /
RUN pip3 install -r /requirements.txt

COPY ./frontend/public/static /static
COPY . /onani

WORKDIR /onani

# Default: dev mode (Flask debug on :5000)
EXPOSE 5000

ENTRYPOINT ["./entrypoints/entrypoint.sh"]