#!/bin/bash

python render_themes_sample.py
gunicorn -b 0.0.0.0:8088 -w 16 server:api
