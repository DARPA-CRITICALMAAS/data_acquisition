#!/bin/bash

# run.sh

mkdir -p ./data

python scrape.py

# Output copied to: `scp -r * rdrive:maps/ngmdb/geotiff/`
# Ask @bkj for details