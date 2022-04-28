#!/bin/bash
# @Author: kapsikkum
# @Date:   2022-03-06 20:54:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-04-28 19:47:43
docker compose -f docker-compose.dev.yml down
docker compose -f docker-compose.dev.yml up -d --build