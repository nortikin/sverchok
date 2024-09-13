#!/usr/bin/python3

# If your blender is not available as just "blender" command, then you need
# to specify path to blender when running this script, e.g.
#
# $ BLENDER=~/soft/blender-2.79/blender ./generate_api_documentation.py
#

import os
import sys

BLENDER = os.environ.get('BLENDER', 'blender')

argv = sys.argv[1:]
argv = ['"' + arg + '"' for arg in argv]
args = " ".join(argv)

os.system(f"{BLENDER} -b --addons sverchok --python utils/apidoc.py --python-exit-code 1 -- {args}")

