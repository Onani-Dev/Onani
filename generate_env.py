# @Author: kapsikkum
# @Date:   2022-03-06 20:54:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-11 14:55:49

import os
import secrets
import string

# Check if the file exsits, if it does we don't need to do anything.
if os.path.exists("./.env"):
    raise FileExistsError(".env File already exists!")

# Generate random values for secret key and database password
DB_PASSWORD = "".join(
    secrets.choice(string.ascii_letters + string.digits) for _ in range(20)
)
FLASK_SECRET_KEY = secrets.token_hex(32)

# Write to .env file
with open(".env", "w") as w:
    w.write(f"DB_PASSWORD={DB_PASSWORD}\n")
    w.write(f"FLASK_SECRET_KEY={FLASK_SECRET_KEY}\n")

print(
    f"""
Generated environment variables:
DB_PASSWORD={DB_PASSWORD}
FLASK_SECRET_KEY={FLASK_SECRET_KEY}

Optional — set these in .env to store data outside Docker named volumes:
  IMAGES_HOST_DIR=/srv/onani/images     # host path for post images
  AVATARS_HOST_DIR=/srv/onani/avatars   # host path for user avatars
  DATABASE_HOST_DIR=/srv/onani/db       # host path for PostgreSQL data

Tip: instead of env vars, you can configure the app with a TOML file.
Copy onani.toml.example to onani.toml, fill in your values, then set:
  ONANI_CONFIG=/path/to/onani.toml
"""
)
