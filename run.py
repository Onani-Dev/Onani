# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2020-11-08 01:35:44
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-10 23:28:39

from Onani import init_app, db

app = init_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
