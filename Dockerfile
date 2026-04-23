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
# Use slim (glibc/Debian) when INSTALL_ML=true because tensorflow has no musl/Alpine wheels.
ARG INSTALL_ML=false
FROM python:3.10-slim AS app-base-true
FROM python:3.10-alpine AS app-base-false
FROM app-base-${INSTALL_ML}

ARG INSTALL_ML=false

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (handles both Alpine and Debian in one block)
RUN if command -v apk >/dev/null 2>&1; then \
        apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev \
        && apk add libffi-dev ffmpeg postgresql-client; \
    else \
        apt-get update && apt-get install -y --no-install-recommends \
            gcc libffi-dev ffmpeg postgresql-client \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Grab Caddy binary from official image
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

# Copy built frontend
COPY --from=frontend-build /app/dist /frontend/dist

COPY requirements.txt requirements-ml.txt /
RUN pip3 install -r /requirements.txt \
    && if [ "$INSTALL_ML" = "true" ]; then pip3 install -r /requirements-ml.txt; fi

COPY ./frontend/public/static /static
COPY . /onani

RUN chmod +x /onani/entrypoints/entrypoint.sh

WORKDIR /onani

EXPOSE 80

ENTRYPOINT ["./entrypoints/entrypoint.sh"]
