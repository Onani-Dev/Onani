# Onani

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![DeepSource](https://deepsource.io/gh/Onani-Dev/Onani.svg/?label=active+issues&show_trend=true&token=5Go--b-mTJBuDqR9HVUjVcMz)](https://deepsource.io/gh/Onani-Dev/Onani/?ref=repository-badge) [![DeepSource](https://deepsource.io/gh/Onani-Dev/Onani.svg/?label=resolved+issues&show_trend=true&token=5Go--b-mTJBuDqR9HVUjVcMz)](https://deepsource.io/gh/Onani-Dev/Onani/?ref=repository-badge)

Docker is required.

Generate a .env file with generate_env.py by using `python generate_env.py` to create a password and secret key.

To run: `./build.sh dev` (Development) or `./build.sh` (Production). 
Onani will then run on http://127.0.0.1:8080/

For default tags, Run `flask tags --filename <meta.json|explicit.json>` inside the onani_flask container. This allows meta and explicit tag checking to work.

To make a user an owner, Run `flask add-owner --id <User ID>` inside the onani_flask container.