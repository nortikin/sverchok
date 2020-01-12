# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from itertools import chain, cycle
import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


def generate_edges(verts_a, verts_b, cuts):
    """
    Generate lines between two given points
    :param verts_a: list of tuple(float, float, float)
    :param verts_b: list of tuple(float, float, float)
    :param cuts: list of int
    :return: numpy array with shape (number of vertices, 3), list of tuple(int, int)
    """
    line_number = max(len(cuts), len(verts_a), len(verts_b))
    verts_number = sum([cuts + 2 if cuts >= 0 else 2 for _, cuts in
                        zip(range(line_number), chain(cuts, cycle([cuts[-1]])))])
    cuts = chain(cuts, cycle([cuts[-1]]))
    verts_a = chain(verts_a, cycle([verts_a[-1]]))
    verts_b = chain(verts_b, cycle([verts_b[-1]]))
    verts_lines = np.empty((verts_number, 3))
    edges_lines = []
    num_added_verts = 0
    indexes = iter(range(int(1e+100)))

    for i, c, va, vb in zip(range(line_number), cuts, verts_a, verts_b):
        va, vb = np.array(va), np.array(vb)
        verts_line = generate_verts(va, vb, c)
        edges_lines.extend([(i, i + 1) for i, _ in zip(indexes, verts_line[:-1])])
        verts_lines[num_added_verts: num_added_verts + len(verts_line)] = verts_line
        num_added_verts += len(verts_line)

    return verts_lines, edges_lines


def generate_verts(va, vb, cuts):
    # interpolate vertices between two given
    if cuts <= 0:
        return np.array((va, vb))
    x = np.linspace(va[0], vb[0], cuts + 2)
    y = np.linspace(va[1], vb[1], cuts + 2)
    z = np.linspace(va[2], vb[2], cuts + 2)
    return np.stack((x, y, z), axis=-1)


def split_lines_to_objects(verts, edges):
    """
    detect lines and split them into separate objects
    vertices and edges should be ordered according generator lines logic
    :param verts: numpy array with shape(n, 3)
    :param edges: list of tuple(int, int)
    :return: list of np arrays, list of list of tuple(int, int)
    """
    split_slice = [0]
    for i in range(len(edges)):
        split_slice[-1] += 1
        # current edge - (0, 1), next edge - (1, 2) - still on the same line
        # current edge - (1, 2), next edge - (3, 4) - the current line is finished
        is_end = True if i + 1 >= len(edges) else True if edges[i][1] != edges[i + 1][0] else False
        if is_end:
            split_slice[-1] += 1
            if i != len(edges) - 1:
                split_slice.append(split_slice[-1])
    edges_out = [[(i, i + 1) for i in range(len(v_num) - 1)]
                 for v_num in np.split(np.empty(len(verts)), split_slice)[:-1]]
    return np.split(verts, split_slice)[:-1], edges_out


class SvSegmentGenerator(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: 2pt Line

    Can subdivide output edge
    Vertices can be as numpy array
    """
    bl_idname = 'SvSegmentGenerator'
    bl_label = 'Segment'
    bl_icon = 'GRIP'
    sv_icon = 'SV_LINE'

    a: bpy.props.FloatVectorProperty(name='A', update=updateNode)
    b: bpy.props.FloatVectorProperty(name='B', default=(0.5, 0.5, 0.5), update=updateNode)
    cuts_number: bpy.props.IntProperty(name='Num cuts', min=0, update=updateNode)
    as_numpy: bpy.props.BoolProperty(name="Numpy output", description="Format of output data", update=updateNode)
    split: bpy.props.BoolProperty(name="Split to objects", description="Each object in separate object",
                                   update=updateNode, default=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'as_numpy')
        layout.prop(self, 'split')

    def rclick_menu(self, context, layout):
        layout.prop(self, 'split')
        layout.prop(self, 'as_numpy')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'A').prop_name = 'a'
        self.inputs.new('SvVerticesSocket', 'B').prop_name = 'b'
        self.inputs.new('SvStringsSocket', 'Cuts').prop_name = 'cuts_number'
        self.outputs.new('SvVerticesSocket', 'Verts')
        self.outputs.new('SvStringsSocket', 'Edges')

    def process(self):
        num_objects = max([len(sock.sv_get(deepcopy=False)) for sock in self.inputs])
        out = []
        for i, a, b, c in zip(
                range(num_objects),
                *[chain(sock.sv_get(deepcopy=False), cycle([sock.sv_get(deepcopy=False)[-1]]))
                  for sock in self.inputs]):
            out.append(generate_edges(a, b, c))
        if self.split:
            temp = [split_lines_to_objects(*data) for data in out]
            out = [v for res in temp for v in zip(*res)]
        if not self.as_numpy:
            out = [(ar.tolist(), edges) for ar, edges in out]
        [sock.sv_set(data) for sock, data in zip(self.outputs, zip(*out))]


def register():
    bpy.utils.register_class(SvSegmentGenerator)


def unregister():
    bpy.utils.unregister_class(SvSegmentGenerator)
