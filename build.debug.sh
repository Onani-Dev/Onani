#!/bin/bash
# @Author: kapsikkum
# @Date:   2022-03-06 20:54:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-07 20:33:16
docker-compose -f "docker-compose.debug.yml" down
docker-compose -f "docker-compose.debug.yml" up -d --build