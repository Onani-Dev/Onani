# Onani

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![DeepSource](https://deepsource.io/gh/Onani-Dev/Onani.svg/?label=active+issues&show_trend=true&token=5Go--b-mTJBuDqR9HVUjVcMz)](https://deepsource.io/gh/Onani-Dev/Onani/?ref=repository-badge) [![DeepSource](https://deepsource.io/gh/Onani-Dev/Onani.svg/?label=resolved+issues&show_trend=true&token=5Go--b-mTJBuDqR9HVUjVcMz)](https://deepsource.io/gh/Onani-Dev/Onani/?ref=repository-badge)

Docker is required.

Generate a .env file with generate.py by using `python generate.py` to create a password and secret key.

To run: `./build.dev.sh` (Development) or `./build.sh` (Production)


For default tags, Run `flask default-tags --filename <meta.json|explicit.json>` inside the onani_flask container. This allows meta and explicit tag checking to work.