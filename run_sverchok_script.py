#!/usr/bin/python3

# If your blender is not available as just "blender" command, then you need
# to specify path to blender when running this script, e.g.
#
# $ BLENDER=~/soft/blender-3.3.1/blender ./run_sverchok_script.py
#

import os
import sys
import argparse

BLENDER = os.environ.get('BLENDER', 'blender')

parser = argparse.ArgumentParser(description = "Run Python script which uses Sverchok API")
parser.add_argument('script', metavar="SCRIPT.PY", help = "Path to Python script file")
parser.add_argument('-b', '--blender', metavar="/PATH/TO/BLENDER", help = "Path to Blender executable", default = BLENDER)

argv = sys.argv[1:]
try:
    delimiter_idx = argv.index("--")
    my_arguments = argv[:delimiter_idx]
    script_arguments = argv[delimiter_idx+1:]
    script_args = " ".join(script_arguments)
except ValueError:
    my_arguments = argv
    script_args = ""

args = parser.parse_args(my_arguments)

command = f"{args.blender} -b --addons sverchok --python {args.script} --python-exit-code 1 -- {script_args}"
print(command)
os.system(command)

