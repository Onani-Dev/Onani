# @Author: kapsikkum
# @Date:   2022-03-06 20:54:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-20 19:35:52

import os
import secrets
import string

DB_PASSWORD = "".join(
    secrets.choice(string.ascii_letters + string.digits) for _ in range(20)
)
FLASK_SECRET_KEY = os.urandom(24)

if os.path.exists("./.env"):
    raise Exception(".env File already exists!")

with open(".env", "w") as w:
    w.write(f"DB_PASSWORD={DB_PASSWORD}\n")
    w.write(f"FLASK_SECRET_KEY={FLASK_SECRET_KEY}\n")
    w.write("RECAPTCHA_PUBLIC_KEY=\n")
    w.write("RECAPTCHA_PRIVATE_KEY=\n")

print(
    f"""Generated environment variables:
DB_PASSWORD={DB_PASSWORD}  
FLASK_SECRET_KEY={FLASK_SECRET_KEY}"""
)
