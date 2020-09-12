# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-12 23:30:09

from OnaniFrontend import create_app, socketio

app = create_app()

if __name__ == "__main__":
    socketio.run(app)
