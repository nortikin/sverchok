#!/bin/bash

set -e

BLENDER=${BLENDER:-blender}
MODULE=$1
shift

$BLENDER -b --addons sverchok --python $MODULE --python-exit-code 1 -- $@

