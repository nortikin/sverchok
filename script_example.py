
# We can import usual python modules here
import sys
import numpy as np

# We can import Blender API
import bpy

# Also we can import Sverchok API modules
from sverchok.utils.testing import link_node_tree, get_node_tree

# Use only arguments which come after --
# ones which come earlier are intended for Blender itself, not for this script
argv = sys.argv
delimiter_idx = argv.index("--")
argv = argv[delimiter_idx+1:]

if len(argv) < 2:
    print("Usage: run_sverchok_script.py script_example.py -- FILE.blend TreeName")
    sys.exit(1)

blend_path = argv[0]
tree_name = argv[1]

# Load node tree. It will be processed upon loading.
link_node_tree(blend_path, tree_name)
tree = get_node_tree(tree_name)

out_buffer = bpy.data.texts['output.txt']
output = out_buffer.as_string()

with open('output.txt', 'wb') as f:
    f.write(output.encode('utf-8'))

