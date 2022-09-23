#!/bin/bash
./art/latesyftlogo.sh

# Metadata ----------------------------------------------------------
# If things hit the fan we'd like to know some build time information
echo "-- RedHat Release --"
cat /etc/redhat-release
echo ""
echo "-- Python Version --"
python --version
echo ""
echo "-- Golang Version --"
go version
echo ""
echo "-- Syft Version --"
syft --version
echo ""
echo "-- Grype Version --"
grype version
echo ""
echo "-- Environment --"
env
echo ""
echo "-- Scanning Workstream --"
echo $WORKSTREAM
echo ""

# Run Python Syft script
echo "Setting up Python environment..."
pipenv install
echo "Twiddling the bits via twiddle-the-bits.py..."
pipenv run python twiddle-the-bits.py $WORKSTREAM

echo ""
./art/fin.sh
