# Onani

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Heh

# Tutorial for Onani setup! (Confidential) (Subject to change)

1. [Setup MongoDB](https://docs.microsoft.com/en-us/windows/wsl/tutorials/wsl-database#install-mongodb) (May vary, Tutorial is for WSL)
1. `python3 -m venv env`
1. `source env/bin/activate`
1. Install dependancies: `pip install -r requirements.txt`
1. Start Gunicorn: `gunicorn -k flask_sockets.worker -w 8 app:app`

Will need tutorial for nginx here also when i get to it.



