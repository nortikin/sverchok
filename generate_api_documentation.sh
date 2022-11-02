#!/bin/bash

# If your blender is not available as just "blender" command, then you need
# to specify path to blender when running this script, e.g.
#
# $ BLENDER=~/soft/blender-2.79/blender ./generate_api_documentation.sh
#

set -e

BLENDER=${BLENDER:-blender}

$BLENDER -b --addons sverchok --python utils/apidoc.py --python-exit-code 1 -- $@

