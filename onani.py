# -*- coding: utf-8 -*-
# @Author: Blakeando
# @Date:   2020-08-12 15:52:51
# @Last Modified by:   Blakeando
# @Last Modified time: 2020-09-17 18:10:53

from OnaniFrontend import init_app, socketio

app = init_app()

if __name__ == "__main__":
    socketio.run(app)
