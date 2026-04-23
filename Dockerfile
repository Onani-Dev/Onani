# Build frontend first
FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# Pull Caddy binary from official image
FROM caddy:2-alpine AS caddy

# All-in-one image: Gunicorn + Caddy reverse proxy
FROM python:3.10-alpine

ARG INSTALL_ML=false

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev \
    && apk add libffi-dev

RUN apk add --no-cache ffmpeg postgresql-client

# Grab Caddy binary from official image
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

# Copy built frontend
COPY --from=frontend-build /app/dist /frontend/dist

COPY requirements.txt requirements-ml.txt /
RUN pip3 install -r /requirements.txt \
    && if [ "$INSTALL_ML" = "true" ]; then pip3 install -r /requirements-ml.txt; fi

COPY ./frontend/public/static /static
COPY . /onani

RUN chmod +x /onani/entrypoints/entrypoint.aio.sh

WORKDIR /onani

EXPOSE 80

ENTRYPOINT ["./entrypoints/entrypoint.aio.sh"]
