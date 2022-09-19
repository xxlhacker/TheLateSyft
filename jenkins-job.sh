#!/bin/bash
echo "================================="
echo "Running The Late Syft Jenkins Job"
echo "================================="
echo ""

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

# Main Logic ---------------------------------------------------------
# Stuff
# Goes
# Here

echo ""
echo "====="
echo "DONE."
echo "====="
