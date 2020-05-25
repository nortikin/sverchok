# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

def gp_macro_one(context, operator, term, nodes, links):
    needed_nodes = [
        ['SvGetAssetPropertiesMK2', (0.00, 0.00)],
        ['SvPathLengthMk2Node', (250, 55)],
        ['SvScalarMathNodeMK4', (430, 115)],
        ['Float2IntNode', (600, 50)],
        ['SvGenNumberRange', (720, 90)],
        ['SvInterpolationNodeMK3', (880, 40)],
        ['LineConnectNodeMK2', (1060, -40)],
        ['SvVDExperimental', (1245, 50)],
    ]

    made_nodes = []
    x, y = context.space_data.cursor_location[:]
    for node_bl_idname, node_location in needed_nodes:
        n = nodes.new(node_bl_idname)
        n.location = node_location[0] + x, node_location[1] + y
        made_nodes.append(n)

    # ID Selector
    made_nodes[0].Mode = 'grease_pencils'  # the rest must be user driven
    links.new(made_nodes[0].outputs[0], made_nodes[1].inputs[0])

    # Scalar Math node
    made_nodes[2].current_op = 'MUL'
    made_nodes[2].y_ = 2.5
    links.new(made_nodes[1].outputs[1], made_nodes[2].inputs[0])   # snlite-> math
    links.new(made_nodes[2].outputs[0], made_nodes[3].inputs[0])   # math -> float

    # Float2Int node
    # made_nodes[3]
    links.new(made_nodes[3].outputs[0], made_nodes[4].inputs[2])

    # Float range
    made_nodes[4].range_mode = 'RANGE_COUNT'
    made_nodes[4].stop_float = 1.0
    links.new(made_nodes[4].outputs[0], made_nodes[5].inputs[1])

    # Vector Interpolate
    made_nodes[5]
    links.new(made_nodes[0].outputs[0], made_nodes[5].inputs[0])
    links.new(made_nodes[5].outputs[0], made_nodes[6].inputs[0])

    # UV connect
    made_nodes[6].polygons = 'Edges'
    made_nodes[6].slice_check = False
    made_nodes[6].dir_check = 'U_dir'

    # Viewer Draw
    made_nodes[7]
    links.new(made_nodes[6].outputs[0], made_nodes[7].inputs[0])
    links.new(made_nodes[6].outputs[1], made_nodes[7].inputs[1])
