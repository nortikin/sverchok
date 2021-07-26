# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import json
from pathlib import Path
import zipfile

import bpy.types
import bmesh
from mathutils import Matrix
import sverchok
from sverchok.core.socket_data import SvGetSocket
from sverchok.utils.tree_structure import Tree
from sverchok.utils.sv_bmesh_utils import pydata_from_bmesh
from sverchok.utils.handle_blender_data import BlNode

"""
import bpy
from sverchok.utils.sv_data_to_json import save_to_file, save_to_json
tree = bpy.data.node_groups['TreeName']
save_to_file(save_to_json(tree), tree.name)
"""


def save_to_json(bl_tree) -> dict:
    """Search output nodes in given tree and save either their output data or if there are no output sockets
    their input data"""
    struct = {}  # node name: node struct
    tree = Tree(bl_tree)
    for node in tree.output_nodes:
        if BlNode(node.bl_tween).base_idname in _ignore_node_ids:
            continue
        node_struct = {}  # socket identifier: data
        data = []
        if node.outputs:
            for sock in node.outputs:
                data = SvGetSocket(sock.bl_tween, sock.bl_tween, False)  # a beat hacky but there is no other way to do
                if data:
                    node_struct[sock.identifier] = _convert_data(data)
        if not data and node.inputs:
            for sock in node.inputs:
                if sock.links:
                    data = sock.bl_tween.sv_get(deepcopy=False)
                    node_struct[sock.identifier] = _convert_data(data)

        struct[node.name] = node_struct
    return struct


def save_to_file(json_data, file_name, path: Path = Path(sverchok.__file__).parent / 'tests/expected_tree_data'):
    with zipfile.ZipFile(path / (file_name + '.zip'), 'w', zipfile.ZIP_DEFLATED) as zip_file:
        with zip_file.open(file_name + '.json', 'w') as file:
            file.write(json.dumps(json_data, indent=2).encode('utf-8'))


# bl id names of nodes which data does not have too much sense to save
_ignore_node_ids = {'NoteNode', 'NodeFrame'}


def _convert_data(data):
    """Convert any data to JSON appropriate format"""
    # todo for now it expects only standard nesting levels
    if isinstance(data[0], (list, tuple)):
        return data
    elif isinstance(data[0], Matrix):
        return [_convert_matrix(m) for m in data]
    elif isinstance(data[0], bpy.types.Object):
        if isinstance(data[0].data, bpy.types.Mesh):
            return [_convert_objects(obj) for obj in data]
        elif isinstance(data[0].data, bpy.types.Curve):
            return [_convert_curve(obj) for obj in data]
        else:
            raise TypeError(f'Unsupported Blender object type: {type(data[0].data)}')
    else:
        raise TypeError(f'Unsupported data type: {type(data[0])}')


def _convert_objects(obj):
    struct = {
        "vertices": [],
        "edges": [],
        "polygons": [],
        "use_smooth": [poly.use_smooth for poly in obj.data.polygons],
        "materials": [_convert_material(mat) for mat in obj.data.materials if mat],
    }
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    struct["vertices"], struct["edges"], struct["polygons"] = pydata_from_bmesh(bm)

    # there is no easy way to check matrix attribute for now - https://developer.blender.org/T90036
    # struct["matrix"] = _convert_matrix(obj.matrix_local)

    return struct


def _convert_material(mat):
    struct = {
        "name": mat.name
    }
    return struct


def _convert_curve(obj):
    struct = []
    spline: bpy.types.Spline
    for spline in obj.data.splines:
        spline_struct = {
            'type': spline.type,
            'use_cyclic_u': spline.use_cyclic_u,
            'use_smooth': spline.use_smooth,
            'vertices': [p.co.to_tuple() for p in spline.points],
            'vertices_radius': [p.radius for p in spline.points],
            'vertices_tilt': [p.tilt for p in spline.points],
        }
        struct.append(spline_struct)
    return struct


def _convert_matrix(mat):
    return [v.to_tuple() for v in mat]
