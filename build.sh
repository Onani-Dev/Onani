#!/bin/bash
# @Author: kapsikkum
# @Date:   2022-03-06 20:54:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-06 22:03:46
# RANDOM_DB_PASSWORD=$(python -c "import secrets; \
# import string; \
# import os; \
# alphabet = string.ascii_letters + string.digits; \
# password = ''.join(secrets.choice(alphabet) for i in range(20)); \
# print(password); \
# ")
# echo "Random password: ${RANDOM_DB_PASSWORD}"
# export RANDOM_DB_PASSWORD=${RANDOM_DB_PASSWORD}
docker-compose -f "docker-compose.debug.yml" down
docker-compose -f "docker-compose.debug.yml" up -d --build