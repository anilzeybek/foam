#!/bin/bash

# Install the package in editable mode
pip3 -m venv myvenv 
source myvenv/bin/activate
pip3 install -e .
pip3 install -r requirements.txt