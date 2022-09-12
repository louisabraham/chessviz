#!/bin/bash
cd "$(dirname "$0")"

gunicorn api:make_app --bind localhost:8082 --worker-class aiohttp.GunicornWebWorker --reload --access-logfile -
