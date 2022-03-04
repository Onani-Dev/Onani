#!/bin/bash
# @Author: kapsikkum
# @Date:   2022-03-02 19:19:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-04 19:45:10
flask init-db
gunicorn -b 0.0.0.0:5000 -w 10 --threads 100 run:app