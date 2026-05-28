#!/usr/bin/env bash
# Direct process initialization management script for tracking environments execution 

export FLASK_APP=manage.py
export FLASK_ENV=development

echo "Launching FX Journal Processing Core Engine at http://127.0.0.1:5000"
python manage.py

