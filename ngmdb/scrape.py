#!/usr/bin/env python

"""
    scrape.py
"""

import argparse
import json
import os
from time import sleep

import pandas as pd
import requests
from bs4 import BeautifulSoup
from joblib import Parallel, delayed
from rich import print
from tqdm import tqdm

# --
# Helpers

def get_all_tiff_mids():
    out   = []
    start = 1
    while start < 7042:
        url = f'https://ngmdb.usgs.gov/ngm-bin/ngm_search_json.pl?Title=&Author=&map_number=&State=&bc_ule=&bc_lre=&g_center=-97.35000,+37.82177&g_zoom=2.312&useextents=&bc_ul=&bc_lr=&publisher_list=usgs&scale=&scale2=&datebgn=&dateend=&format=gtiff&start={start}'
        print(f"Request with start: {start}...")
        res = requests.get(url, headers={
            'User-Agent'       : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
            'Accept'           : 'application/json, text/javascript',
            'Accept-Language'  : 'en-US,en;q=0.5',
            'Accept-Encoding'  : 'gzip, deflate, br',
            'X-Requested-With' : 'XMLHttpRequest',
            'Connection'       : 'keep-alive',
            'Referer'          : 'https://ngmdb.usgs.gov/ngm-bin/ngm_search_dbi.pl?Title=&Author=&map_number=&State=&bc_ule=&bc_lre=&g_center=-97.35000%2C+37.82177&g_zoom=2.312&useextents=&bc_ul=&bc_lr=&publisher_list=usgs&scale=&scale2=&datebgn=&dateend=&format=gtiff',
            'Sec-Fetch-Dest'   : 'empty',
            'Sec-Fetch-Mode'   : 'cors',
            'Sec-Fetch-Site'   : 'same-origin',
        }).json()
        
        out += res['ngmdb_catalog_search']['results']
        
        start += 100
        print(len(out), "results gathered")
        sleep(2)
        
    df_out = pd.DataFrame(out)
    df_out = df_out.sort_values('id').reset_index(drop=True)
    return df_out

def get_meta(mid):
    res = requests.get(f'https://ngmdb.usgs.gov/Prodesc/proddesc_{mid}.htm', headers={
        'User-Agent'                : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept'                    : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language'           : 'en-US,en;q=0.5',
        'Accept-Encoding'           : 'gzip, deflate, br',
        'Connection'                : 'keep-alive',
        'Upgrade-Insecure-Requests' : '1',
        'Sec-Fetch-Dest'            : 'document',
        'Sec-Fetch-Mode'            : 'navigate',
        'Sec-Fetch-Site'            : 'none',
        'Sec-Fetch-User'            : '?1',
        'If-Modified-Since'         : 'Fri, 07 Jul 2023 15:49:48 GMT',
        'If-None-Match'             : '"55ef-5ffe7952d04ce"',
    })
    
    if res.status_code != 200:
        return None
    
    soup = BeautifulSoup(res.text, 'lxml')
    for s in soup.findAll('script'):
        if 'holdings' in s.text:
            data = s.text.strip().replace('var holdings = ', '')
            return json.loads(data)
    
    return None


def get_file(item_id, mid):
    return requests.get(f'https://ngmdb.usgs.gov/ngm-bin/pdp/download.pl?q={item_id}_{mid}_5', headers={
        'User-Agent'                : 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Accept'                    : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language'           : 'en-US,en;q=0.5',
        'Accept-Encoding'           : 'gzip, deflate, br',
        'Connection'                : 'keep-alive',
        'Referer'                   : f'https://ngmdb.usgs.gov/Prodesc/proddesc_{mid}.htm',
        'Upgrade-Insecure-Requests' : '1',
        'Sec-Fetch-Dest'            : 'document',
        'Sec-Fetch-Mode'            : 'navigate',
        'Sec-Fetch-Site'            : 'same-origin',
        'Sec-Fetch-User'            : '?1',
    })


def _is_tiff(d):
    # !! UNTESTEd
    # fmt==5 -> tiff ; geo=='true' -> geotiff
    return (d['fmt'] == 5) # and (d['geo'] == 'true')


def get_tiffs(mid, outdir='data'):
    meta = get_meta(mid)
    if meta is None:
        print(f'{mid}: meta is None')
        return
    
    if 'images' not in meta:
        print(f'{mid}: `images` not in meta')
        return
    
    for image in meta['images']:
        item_id = image['item']
        
        tiffs = [d for d in image['downloads'] if _is_tiff(d)]
        if len(tiffs) > 1:  raise Exception()
        if len(tiffs) == 0: 
            print(f'{mid}: len(tiffs) == 0')
            continue
        
        is_gtiff = 'geo' in tiffs[0]
        ext      = 'zip' if is_gtiff else 'tif'
        outpath  = os.path.join(outdir, f"{mid:06d}", f"{item_id}_{mid}.{ext}")
        if os.path.exists(outpath):
            print(f'{outpath} exists')
            continue
        
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        
        data = get_file(item_id, mid)
        with open(outpath, "wb") as f:
            _ = f.write(data.content)

# --
# Run

if not os.path.exists('all_tiff.tsv'):
    get_all_tiff_mids().to_csv('all_tiff.tsv', sep='\t', index=False)

df_tiff = pd.read_csv('all_tiff.tsv', sep='\t')

jobs = []
for mid in df_tiff.id.values:
    
    if os.path.exists(f'data/{mid:06d}'): 
        print(f'skipping {mid:06d}')
        continue
    
    jobs.append(delayed(get_tiffs)(mid))

_ = Parallel(backend='multiprocessing', verbose=10, n_jobs=1)(jobs)