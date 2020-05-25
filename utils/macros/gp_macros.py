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
        ['SvInterpolationNodeMK3', (680, 40)],
        ['LineConnectNodeMK2', (860, -40)],
        ['SvVDExperimental', (1045, 50)],
    ]

    made_nodes = []
    x, y = context.space_data.cursor_location[:]
    for node_bl_idname, node_location in needed_nodes:
        n = nodes.new(node_bl_idname)
        n.location = node_location[0] + x, node_location[1] + y
        made_nodes.append(n)

    # nodes!
    obj_id, path_len, scalar_math, vec_int, uv_con, drawnode = made_nodes

    # -- node settings --
    obj_id.Mode = 'grease_pencils' 
    vec_int.infer_from_integer_input = True
    scalar_math.current_op = 'MUL'
    scalar_math.y_ = 2.5
    uv_con.polygons = 'Edges'
    uv_con.slice_check = False
    uv_con.dir_check = 'U_dir'

    # ID Selector -> pathlen and vector interpolate
    links.new(obj_id.outputs[0], path_len.inputs[0])
    links.new(obj_id.outputs[0], vec_int.inputs[0])

    # pathlen -> Vec int.
    links.new(path_len.outputs[1], scalar_math.inputs[0])
    
    # Scalar Math node -> vec int
    links.new(scalar_math.outputs[0], vec_int.inputs[1])

    # Vector Interpolate -> uv
    links.new(vec_int.outputs[0], uv_con.inputs[0])

    # uvcon -> Viewer Draw
    links.new(uv_con.outputs[0], drawnode.inputs[0])
    links.new(uv_con.outputs[1], drawnode.inputs[1])
