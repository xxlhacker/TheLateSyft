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
echo "-- Scanning Quay.io Image --"
echo $QUAY_IMAGE:$QUAY_TAG
echo ""
if [ $SYFT_OUTPUT_FORMAT = "template" ]; then
    SYFT_OUTPUT_TEMPLATE_FILE="syft-output-template.tmpl"
    echo $SYFT_OUTPUT_TEMPLATE > $SYFT_OUTPUT_TEMPLATE_FILE
fi
mkdir $WORKSPACE/syft_results
syft $QUAY_IMAGE:$QUAY_TAG -o $SYFT_OUTPUT_FORMAT=$WORKSPACE/syft_results/$QUAY_IMAGE.$OUTPUT_FORMAT $SYFT_OUTPUT_TEMPLATE_FILE
echo ""

echo ""
echo "====="
echo "DONE."
echo "====="
