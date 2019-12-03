#!/bin/bash

python render_connect4_themes.py
gunicorn -b 0.0.0.0:8088 -w 16 server:api
