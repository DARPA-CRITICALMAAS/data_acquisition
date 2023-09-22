# ngmdb

Programmatically obtaining data .tif data from https://ngmdb.usgs.gov/ngmdb/ngmdb_home.html

## Important

**Before you run this, please contact Jataware directly at justin@jataware.com or ben@jataware.com for access to the already scraped data such that no one hammers the ngmdb site unnecessarily.
This is a long running process that repeatedly hits the ngmdb site.**

## What it does
This code builds an index of the .tif files on the site (`all_tiff.tsv`) and then logs the metadata and downloads the files.

The `all_tiff.tsv` file is a snapshot version (as of 09/22/2023) of this index and can be rebuilt by simply deleting the file before running.  **Please note if you do this, it may take some time to rebuild the index as there are 7044++ .tifs and each network call returns only 100 results.**

The downloading of the .tif files occurs via the creation of corresponding zero-padded directories of `.zip` files containing the raw .tif files for each row in the `all_tiff.tsv` file.  The `id` field in this file lines up with the associated `./data/<id>` directory.

## Install

`pip install -r requirements.txt`

## Usage

`./run.sh`