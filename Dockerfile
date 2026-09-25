# Global ARG must be declared before any FROM to be usable in FROM line interpolation.
# Use slim (glibc/Debian) when INSTALL_ML=true because tensorflow has no musl/Alpine wheels.
ARG INSTALL_ML=false

# Build frontend first
FROM node:22-alpine AS frontend-build
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend .
RUN npm run build

# Pull Caddy binary from official image
FROM caddy:2-alpine AS caddy

# Base image variants — selected via INSTALL_ML build arg
FROM python:3.10-slim AS app-base-true
FROM python:3.10-alpine AS app-base-false
FROM app-base-${INSTALL_ML}

# Re-declare after FROM so it is available in the build stage
ARG INSTALL_ML=false

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system deps (handles both Alpine and Debian in one block)
RUN if command -v apk >/dev/null 2>&1; then \
        apk add --update --no-cache --virtual .tmp-build-deps gcc libc-dev \
        && apk add libffi-dev ffmpeg postgresql-client dcron; \
    else \
        apt-get update && apt-get install -y --no-install-recommends \
            gcc libffi-dev ffmpeg postgresql-client cron \
        && rm -rf /var/lib/apt/lists/*; \
    fi

# Unprivileged user gunicorn/caddy run as. Root is still needed at container
# start (cron, migrations, chowning volume-mounted dirs) — entrypoint.sh
# drops to this user only for the two processes that serve network traffic.
RUN if command -v apk >/dev/null 2>&1; then \
        addgroup -g 1000 app && adduser -D -u 1000 -G app app; \
    else \
        groupadd -g 1000 app && useradd -m -u 1000 -g app app; \
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

# Keep a pristine copy of the migration versions so the entrypoint can sync
# them into a volume-mounted /onani/migrations/versions on startup.
RUN cp -r /onani/migrations /onani/migrations_bundled

RUN chmod +x /onani/entrypoints/entrypoint.sh

# Default runtime dirs for the unprivileged user; volume mounts overriding
# these are re-chowned by entrypoint.sh at startup since a fresh Docker
# volume/bind mount is root-owned regardless of what the image sets here.
RUN mkdir -p /images /avatars /logs \
    && chown -R app:app /onani /static /images /avatars /logs

WORKDIR /onani

# Caddy listens on :8080 (not :80) so it can be started as the unprivileged
# app user — binding <1024 needs root or cap_net_bind_service. Map the host's
# port 80/443 to this container's 8080 in compose/your reverse proxy instead.
EXPOSE 8080

ENTRYPOINT ["./entrypoints/entrypoint.sh"]
