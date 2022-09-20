#!/bin/bash
echo "================================="
echo "Running The Late Syft Jenkins Job"
echo "================================="
echo ""
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

# Main Logic ---------------------------------------------------------
# Stuff
# Goes
# Here
echo "-- Scanning Quay.io Image --"
echo $QUAY_IMAGE:$QUAY_TAG
echo ""

# Make the artifacts results directory
RESULTS_DIR=$WORKSPACE"/syft_results"
echo "Making artifacts results directory "$RESULTS_DIR"..."
mkdir $RESULTS_DIR

# Determine output template format
if [ $SYFT_OUTPUT_FORMAT = "template" ]; then
    SYFT_OUTPUT_TEMPLATE_FILE_FLAG="-t templates/"$SYFT_OUTPUT_TEMPLATE_FILE
else
    SYFT_OUTPUT_TEMPLATE_FILE_FLAG=""
fi

# Sanitize any bad strings for artifact filenames
FORMATTED_QUAY_IMAGE=$(echo $QUAY_IMAGE | sed -e 's/[^A-Za-z0-9._-]/_/g')
SYFT_OUTPUT_FILE=$RESULTS_DIR"/"$FORMATTED_QUAY_IMAGE"."$SYFT_OUTPUT_FORMAT

# Perform Syft Analysis
echo "Writing Syft results to file "$SYFT_OUTPUT_FILE"..."
syft $QUAY_IMAGE:$QUAY_TAG -o $SYFT_OUTPUT_FORMAT=$SYFT_OUTPUT_FILE $SYFT_OUTPUT_TEMPLATE_FILE_FLAG
echo ""

echo ""
./fin.sh
