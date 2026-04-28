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

# Grab Caddy binary from official image
COPY --from=caddy /usr/bin/caddy /usr/bin/caddy

# Copy built frontend
COPY --from=frontend-build /app/dist /frontend/dist

COPY requirements.txt requirements-ml.txt /
RUN pip3 install -r /requirements.txt \
    && if [ "$INSTALL_ML" = "true" ]; then \
        pip3 install -r /requirements-ml.txt; \
        # requirements-ml.txt installs tensorflow-rocm on Python<3.13, which
        # requires libhsa-runtime64 (AMD ROCm) at import time.  Docker images
        # run CPU-only, so force-replace it with the CPU-only wheel.
        pip3 install --force-reinstall --no-deps tensorflow-cpu; \
    fi

COPY ./frontend/public/static /static
COPY . /onani

# Keep a pristine copy of the migration versions so the entrypoint can sync
# them into a volume-mounted /onani/migrations/versions on startup.
RUN cp -r /onani/migrations /onani/migrations_bundled

RUN chmod +x /onani/entrypoints/entrypoint.sh

WORKDIR /onani

EXPOSE 80

ENTRYPOINT ["./entrypoints/entrypoint.sh"]
