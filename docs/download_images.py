#!/usr/bin/python3

#
# Downloads all images referenced from the documentation
# and replaces corresponding references within rst files.
# NB: this script updates existing rst files!
# do not commit such changes.
#

import re
from urllib.request import urlretrieve
from os.path import join, dirname, basename, exists, relpath
from os import walk
from glob import fnmatch
from logging import info, error
import logging

URL_RE = re.compile(r"https://.*\.png", re.IGNORECASE)

logging.basicConfig(level = logging.INFO)

def download_image(url):
    dst = join("_build", "html", "_static", "images", basename(url))
    if exists(dst):
        info("  Already was downloaded: %s", dst)
        return dst
    else:
        try:
            urlretrieve(url, dst)
            info("  Downloaded: %s => %s", url, dst)
            return dst
        except Exception as e:
            error("Can't download %s: %s", url, e)
            return url

def process_rst(path):
    info("Processing: %s", path)
    output = ""
    with open(path, 'r') as rst:
        for line in rst:
            urls = URL_RE.findall(line)
            for url in urls:
                dst = download_image(url)
                line = line.replace(url, relpath(dst, dirname(path)))
            output = output + line

    with open(path, 'w') as rst:
        rst.write(output)

for directory, subdirs, fnames in walk("."):
    for fname in fnames:
        if fnmatch.fnmatch(fname, "*.rst"):
            process_rst(join(directory, fname))

