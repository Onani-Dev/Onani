# -*- coding: utf-8 -*-
# @Author: kapsikkum
# @Date:   2021-01-05 18:19:14
# @Last Modified by:   kapsikkum
# @Last Modified time: 2021-01-11 03:16:24


from Onani import init_app, db

app = init_app()
try:
    db.drop_all(app=app)
except Exception as e:
    print("Unable to drop DB,", e)
else:
    print("Dropped DB")
    try:
        db.create_all(app=app)
    except Exception as e:
        print("Unable to create DB,", e)
    else:
        print("Created DB")