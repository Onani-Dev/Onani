#!/bin/sh
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-26 00:31:28
flask db init
flask init-db
flask db migrate
gunicorn -b 0.0.0.0:5000 -w 10 --threads 100 run:app