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

# example:
# 124717678-6c0d0800-df16-11eb-83fa-b9f6d21c417a.png
URL_RE_PNG = re.compile(r"https://.*\.png", re.IGNORECASE)
URL_RE_JPG = re.compile(r"https://.*\.jpg", re.IGNORECASE)
URL_RE_GIF = re.compile(r"https://.*\.gif", re.IGNORECASE)
URL_RE_NUM = re.compile(r'https://.*[\da-z]*-[\da-z]*-[\da-z]*-[\da-z]*-[\da-z]*', re.IGNORECASE)

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

def process_rst(path,pas):
    info("Processing: %s", path)
    output = ""
    with open(path, 'r') as rst:
        for line in rst:
            if pas == 1:
                urlsP = URL_RE_PNG.findall(line)
                urlsJ = URL_RE_JPG.findall(line)
                urlsG = URL_RE_GIF.findall(line)
                for url in (*urlsP,*urlsJ,*urlsG):
                    dst = download_image(url)
                    line = line.replace(url, relpath(dst, dirname(path)))
            elif pas == 2:
                urlsN = URL_RE_NUM.findall(line)
                for url in urlsN:
                    dst = download_image(url)
                    line = line.replace(url, relpath(dst, dirname(path)))
            output = output + line

    with open(path, 'w') as rst:
        rst.write(output)

def passing(pas=1):
    for directory, subdirs, fnames in walk("."):
        for fname in fnames:
            if fnmatch.fnmatch(fname, "*.rst"):
                process_rst(join(directory, fname), pas)


if __name__ == '__main__':
    passing(1)
    passing(2)
