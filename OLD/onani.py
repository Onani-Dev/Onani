# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   kapsikkum
# @Last Modified time: 2020-11-08 01:41:11

from OnaniFrontend import init_app, socketio

app = init_app()

if __name__ == "__main__":
    socketio.run(app)
