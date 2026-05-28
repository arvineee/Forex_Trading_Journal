#!/usr/bin/env bash
# Termux automated environmental compilation framework configuration script

echo "============ STARTING FOREX JOURNAL LOCAL APP SETUP ============"

# Upgrade baseline local packages inside Termux system environment securely
pkg update -y && pkg upgrade -y

# Verify and acquire dependencies natively required for Python environment building blocks
pkg install -y python python-pip tur-repo sqlite

# Complete pip installation parameters setup execution
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database mapping migrations cleanly via system application factory commands
export FLASK_APP=manage.py
flask seed-db

echo "============ SYSTEM ARCHITECTURE PREPARATION COMPLETED ============"
echo "Execute command 'bash run.sh' to activate backend local processing servers."

