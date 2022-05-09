#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-04-12 03:41:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-28 19:46:33

# Initialize the database if it has not been already.
flask db init
flask init-db

# Detect database changes.
flask db migrate

# Run the gunicorn webserver
gunicorn -b 0.0.0.0:5000 -w 20 --threads 100 run:app --reload