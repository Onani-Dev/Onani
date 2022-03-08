#!/bin/bash
# @Author: kapsikkum
# @Date:   2022-03-06 20:54:49
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 00:34:47
docker-compose -f "docker-compose.yml" down
docker-compose -f "docker-compose.yml" up -d --build