#!/bin/bash
./latesyftlogo.sh

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
echo "-- Environment --"
env
echo ""
echo "-- Scanning Workstream --"
echo $WORKSTREAM
echo ""
echo "-- Output Format --"
echo $OUTPUT_FORMAT" "$OUTPUT_TEMPLATE
echo ""

# Make the artifacts results directory
RESULTS_DIR=$WORKSPACE"/syft_results"
echo "Making artifacts results directory "$RESULTS_DIR
mkdir $RESULTS_DIR

# Run Python Syft script
echo "Setting up Python environment..."
pipenv install
echo "Running syft-automation.py..."
pipenv run python syft-automation.py $WORKSTREAM

echo ""
./fin.sh
