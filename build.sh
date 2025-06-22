#!/bin/bash
pip install -r requirements.txt
gunicorn --worker-class geventwebsocket.gunicorn.workers.GeventWebSocketWorker --bind 0.0.0.0:5000 app:app
