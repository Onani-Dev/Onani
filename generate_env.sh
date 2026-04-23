#!/bin/sh

set -eu

if [ -f ./.env ]; then
	echo ".env file already exists" >&2
	exit 1
fi

DB_PASSWORD=$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 20)
FLASK_SECRET_KEY=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')

cat > ./.env <<EOF
DB_PASSWORD=${DB_PASSWORD}
FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
EOF

cat <<EOF
Generated environment variables:
DB_PASSWORD=${DB_PASSWORD}
FLASK_SECRET_KEY=${FLASK_SECRET_KEY}

Optional - set these in .env to store data outside Docker named volumes:
  IMAGES_HOST_DIR=/srv/onani/images     # host path for post images
  AVATARS_HOST_DIR=/srv/onani/avatars   # host path for user avatars
  DATABASE_HOST_DIR=/srv/onani/db       # host path for PostgreSQL data

Tip: instead of env vars, you can configure the app with a TOML file.
Copy onani.toml.example to onani.toml, fill in your values, then set:
  ONANI_CONFIG=/path/to/onani.toml
EOF