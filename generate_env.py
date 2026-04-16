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
"""
)
