'''Script for creating a XYZ style basemap for all NAIP imagery for a given (state, year).

This goes really fast on Azure VMs in US East with large number of cores.
'''
import sys
import os
import time
import subprocess
from multiprocessing import Pool

import numpy as np

NAIP_BLOB_ROOT = 'https://naipblobs.blob.core.windows.net/naip'

OUTPUT_DIR = "/home/caleb/data/oh_2017_naip/"
OUTPUT_TILE_DIR = "/home/caleb/data/oh_2017_naip_tiles/"
NUM_WORKERS = 64
STATE = "oh" # use state code
YEAR = 2017

# TODO: download in a cross-platform friendly way, save to tempfile, remove after use. 
if not os.path.exists("naip_v002_index.csv"):
    os.system("wget 'https://naipblobs.blob.core.windows.net/naip-index/naip_v002_index.zip'")
    os.system("unzip naip_v002_index.zip")
    os.remove("naip_v002_index.zip")

fns = []
with open("naip_v002_index.csv", "r") as f:    
    for line in f:
        line = line.strip()
        if line != "":
            if line.endswith(".tif"):
                if ("/%s/" % (STATE)) in line and ("/%d/" % (YEAR)) in line:
                    fns.append(line)

def do_work(fn):
    time.sleep(np.random.random()*2)
    
    url = NAIP_BLOB_ROOT + "/" + fn
    output_fn = fn.split("/")[-1]
    output_tmp_fn = output_fn[:-4] + "_tmp.tif"
    
    command = [
        "GDAL_SKIP=DODS",
        "gdalwarp",
        "-t_srs", "epsg:3857",
        "'%s'" % (url),
        OUTPUT_DIR + output_tmp_fn
    ]
    subprocess.call(" ".join(command), shell=True)
    
    
    command = [
        "gdal_translate",
        "-b", "1", "-b", "2", "-b", "3",
        OUTPUT_DIR + output_tmp_fn,
        OUTPUT_DIR + output_fn
    ]
    subprocess.call(" ".join(command), shell=True)
    
    os.remove(OUTPUT_DIR + output_tmp_fn)

p = Pool(NUM_WORKERS)
_ = p.map(do_work, fns)



command = [
    "gdalbuildvrt", "-srcnodata", "\"0 0 0\"", "basemap.vrt", "%s*.tif" % (OUTPUT_DIR)
]
subprocess.call(" ".join(command), shell=True)


for zoom_level in range(8,17):
   print("Running zoom level $i")
   command = [
       "gdal2tiles.py", "-z", str(zoom_level), "--processes=%d" % (NUM_WORKERS), "basemap.vrt", OUTPUT_TILE_DIR
   ]
   subprocess.call(" ".join(command), shell=True)