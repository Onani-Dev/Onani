#!/bin/bash
# @Author: kapsikkum
# @Date:   2022-04-12 03:41:45
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-12 03:42:03
flask db init
flask init-db
flask db migrate
gunicorn -b 0.0.0.0:5000 -w 10 --threads 100 run:app --reload