# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2022-03-09 02:57:16
# @Last Modified by:   kapsikkum
# @Last Modified time: 2022-03-09 02:58:00
import traceback

from . import main


@main.app_errorhandler(Exception)
def error_handler(e):
    print(traceback.print_tb(e.__traceback__))  # DEBUG
    return str(e)
