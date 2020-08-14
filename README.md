# Onani

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

# Tutorial for Onani setup (Subject to change)

## Setup MongoDB (Ubuntu 20.04 LTS)
1. Import the MongoDB public GPG Key: `wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -`

1. Create the list file: `echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list` 
(Ubuntu 20.04 only)

1. Update the package DB: `sudo apt update`

1. Install the MongoDB package: `sudo apt install mongodb-org`

1. Start the MongoDB service: `sudo systemctl start mongod` (Run `sudo systemctl daemon-reload` if you get `Failed to start mongod.service: Unit mongod.service not found.`)

1. Verify that MongoDB has started: `sudo systemctl status mongod`

1. Enable MongoDB startup on boot: `sudo systemctl enable mongod` (Optional)

## Setup Virtualenv
1. `sudo pip install virtualenv` (If not already installed)

1. `virtualenv -p python3 env` (Only do once.)

1. `. env/bin/activate`

You should only need to use the `. env/bin/activate` command once you have done step 1 and 2.

## Setup Gunicorn
1. Install Onani dependancies: `pip install -r requirements.txt`

1. Start Gunicorn: `gunicorn -k flask_sockets.worker -w 8 app:app`

## Setup nginx
TODO



