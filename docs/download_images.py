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
from concurrent.futures import ThreadPoolExecutor
import argparse

# example:
# 124717678-6c0d0800-df16-11eb-83fa-b9f6d21c417a.png
URL_RE_PNG = re.compile(r"https://.*\.png", re.IGNORECASE)
URL_RE_JPG = re.compile(r"https://.*\.jpg", re.IGNORECASE)
URL_RE_GIF = re.compile(r"https://.*\.gif", re.IGNORECASE)
URL_RE_NUM = re.compile(r'https://.*[\da-z]*-[\da-z]*-[\da-z]*-[\da-z]*-[\da-z]*', re.IGNORECASE)

logging.basicConfig(level = logging.INFO)

def download_image(args, url):

    if args.target:
        dst = join(args.target, basename(url))
    else:
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

def process_rst(path, args, pas):
    info("Processing: %s", path)
    output = ""
    with open(path, 'r') as rst:
        for line in rst:
            if pas == 1:
                urlsP = URL_RE_PNG.findall(line)
                urlsJ = URL_RE_JPG.findall(line)
                urlsG = URL_RE_GIF.findall(line)
                for url in (*urlsP,*urlsJ,*urlsG):
                    dst = download_image(args, url)
                    if args.edit:
                        line = line.replace(url, relpath(dst, dirname(path)))
            elif pas == 2:
                urlsN = URL_RE_NUM.findall(line)
                for url in urlsN:
                    dst = download_image(args, url)
                    if args.edit:
                        line = line.replace(url, relpath(dst, dirname(path)))
            if args.edit:
                output = output + line

    if args.edit:
        with open(path, 'w') as rst:
            rst.write(output)

def is_excluded(args, name):
    for item in name.split('/'):
        for pattern in args.exclude:
            if fnmatch.fnmatch(item, pattern):
                return True
    return False

def iterate_files(args):
    for directory, subdirs, fnames in walk(args.path):
        if is_excluded(args, directory):
            continue
        for fname in fnames:
            if is_excluded(args, fname):
                continue
            if fnmatch.fnmatch(fname, "*.rst"):
                yield join(directory, fname)

def passing(args, pas=1):
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for path in iterate_files(args):
            executor.submit(process_rst, path, args, pas)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="Download Images")
    parser.add_argument('-e', '--edit', action='store_true', help="Edit source text and replace image URLs with paths to downloaded images")
    parser.add_argument('-j', '--threads', nargs='?', type=int, default=1, metavar="N", help="Download images in several threads")
    parser.add_argument('-t', '--target', nargs='?', metavar="PATH", help="Path to target directory with images")
    parser.add_argument('-E', '--exclude', action='append', help="Exclude file or directory name")
    parser.add_argument('path', default=".", metavar="DIRECTORY", help="Path to directory with source texts")
    args = parser.parse_args()
    #print(args)

    passing(args, 1)
    passing(args, 2)
