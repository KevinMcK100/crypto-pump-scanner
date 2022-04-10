#!/bin/bash

# Pull latest code from git repo
git pull origin master

# Install dependencies in virtual environment
if [ ! -d venv ]; then
    python3.9 -m venv .venv
fi
# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip
# Install pip-tools to compile dependencies
python -m pip install pip-tools
# Compile dependencies and update requirements.txt
python -m piptools compile --upgrade requirements.in
# Install dependencies
pip3 install -r requirements.txt

jupyter lab crypto_pump_scanner.ipynb