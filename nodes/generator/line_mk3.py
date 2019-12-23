# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from itertools import chain, cycle
import numpy as np

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


directionItems = [
    ("X",  "X",  "Along X axis",         0),
    ("Y",  "Y",  "Along Y axis",         1),
    ("Z",  "Z",  "Along Z axis",         2),
    ("AB", "AB", "Between 2 points",     3),
    ("OD", "OD", "Origin and Direction", 4),
    ]


def make_line(numbers, steps, sizes, mode='X', normalized=False, center=False):
    """
    Generate simple lines along X, Y or Z axis. All lines locates in one object.
    :param numbers: Number of vertices, list of int
    :param steps: Step length, list of float
    :param sizes: Size of lines in normalized mode, list of floats
    :param mode: 'X' or 'Y' or 'Z'
    :param normalized: fit line into given size
    :param center: move center of line in center of coordinates
    :return: np.array of vertices, np.array of edges
    """
    number_of_lines = max(len(numbers), len(sizes), len(steps))
    number_of_edges = sum([v_number - 1 if v_number > 1 else 1 for _, v_number in
                           zip(range(number_of_lines), chain(numbers, cycle([numbers[-1]])))])
    number_of_vertices = sum([v_number if v_number > 1 else 2 for _, v_number in
                           zip(range(number_of_lines), chain(numbers, cycle([numbers[-1]])))])
    numbers = chain(numbers, cycle([numbers[-1]]))
    steps = chain(steps, cycle([steps[-1]]))
    sizes = chain(sizes, cycle([sizes[-1]]))
    verts_lines = np.empty((number_of_vertices, 3))
    edges_lines = np.empty((number_of_edges, 2))
    num_added_edges = 0
    num_added_verts = 0

    for i_line, n, st, size in zip(range(number_of_lines), numbers, steps, sizes):
        n = 2 if n < 2 else n
        if normalized and center:
            co1, co2 = -size / 2, size / 2
        elif normalized:
            co1, co2 = 0, size
        elif center:
            co1, co2 = -st * (n - 1) / 2, st * (n - 1) / 2
        else:
            co1, co2 = 0, st * (n - 1)
        va = np.array((co1 if mode == "X" else 0, co1 if mode == "Y" else 0, co1 if mode == "Z" else 0))
        vb = np.array((co2 if mode == "X" else 0, co2 if mode == "Y" else 0, co2 if mode == "Z" else 0))
        edges_lines[num_added_edges: num_added_edges + n - 1] = np.stack([np.arange(n - 1), np.arange(1, n)], axis=1)
        verts_lines[num_added_verts: num_added_verts + n] = (generate_verts(va, vb, n))
        num_added_edges += n - 1
        num_added_verts += n
    return verts_lines, edges_lines


def make_line_advanced(numbers, steps, sizes, verts_a, verts_b, mode='AB', normalized=False, center=False):
    """
    Generate lines between two given points in 'AB' mode or determined by origin(vert_a) and direction(vert_b)
    :param numbers: Number of vertices, list of int
    :param steps: Step length, list of float
    :param sizes: Size of lines in normalized mode, list of floats
    :param verts_a: or origin, list of vertices
    :param verts_b: or direction, list of vertices
    :param mode: 'AB' - generate line between points, 'OD' - generate line from origin with determined direction
    :param normalized: fit line into given size
    :param center: move center of line into vert_a
    :return: list of vertices, list of edges (*one object)
    """
    max_len = max(len(numbers), len(steps), len(sizes), len(verts_a), len(verts_b))
    numbers = chain(numbers, cycle([numbers[-1]]))
    steps = chain(steps, cycle([steps[-1]]))
    sizes = chain(sizes, cycle([sizes[-1]]))
    verts_a = chain(verts_a, cycle([verts_a[-1]]))
    verts_b = chain(verts_b, cycle([verts_b[-1]]))
    verts_lines = []
    edges_lines = []

    for i, n, st, size, va, vb in zip(range(max_len), numbers, steps, sizes, verts_a, verts_b):
        va, vb = np.array(va), np.array(vb)
        if normalized or center:
            # if center is true then va becomes center

            if mode == 'AB':
                len_line = np.linalg.norm(vb - va)
                dir_line = (vb - va) * 1 / len_line
            else:
                len_line = st * (n - 1 if n > 2 else 1)
                dir_line = vb * 1 / np.linalg.norm(vb)

            if normalized and center:
                verts_line = generate_verts(va + dir_line * (-size / 2), va + dir_line * (size / 2), n)
            elif normalized:
                verts_line = generate_verts(va, va + dir_line * size, n)
            elif center:
                verts_line = generate_verts(va + dir_line * (-len_line / 2), va + dir_line * (len_line / 2), n)
        else:
            if mode == 'AB':
                verts_line = generate_verts(va, vb, n)
            else:
                len_line = st * (n - 1 if n > 2 else 1)
                dir_line = vb * 1 / np.linalg.norm(vb)
                verts_line = generate_verts(va, va + dir_line * len_line, n)

        edges_lines.extend((i + len(verts_lines), i + len(verts_lines) + 1) for i in range(1 if n <= 2 else n - 1))
        verts_lines.extend(verts_line.tolist())
    return verts_lines, edges_lines


def generate_verts(va, vb, number):
    # interpolate vertices between two given
    if number <= 2:
        return np.array((va, vb))
    x = np.linspace(va[0], vb[0], number)
    y = np.linspace(va[1], vb[1], number)
    z = np.linspace(va[2], vb[2], number)
    return np.stack((x, y, z), axis=-1)


def split_lines_to_objects(verts, edges):
    # detect lines and split them into separate objects
    # vertices and edges should be ordered according generator lines logic
    verts = iter(verts)
    verts_out = [[]]

    for i in range(len(edges)):
        verts_out[-1].append(next(verts))
        # current edge - (0, 1), next edge - (1, 2) - still on the same line
        # current edge - (1, 2), next edge - (3, 4) - the current line is finished
        is_end = True if i + 1 >= len(edges) else True if edges[i][1] != edges[i + 1][0] else False
        if is_end:
            verts_out[-1].append(next(verts))
            if i != len(edges) - 1:
                verts_out.append([])
    edges_out = [[(i, i + 1) for i in range(len(vs) - 1)] for vs in verts_out]
    return verts_out, edges_out


class SvLineNodeMK3(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Line, segment.
    Tooltip: Generate line.
    """
    bl_idname = 'SvLineNodeMK3'
    bl_label = 'Line'
    bl_icon = 'GRIP'
    sv_icon = 'SV_LINE'

    def update_size_socket(self, context):
        """ need to do UX transformation before updating node"""
        self.inputs["Size"].hide_safe = not self.normalize
        updateNode(self, context)

    def update_vect_socket(self, context):
        """ need to do UX transformation before updating node"""
        si = self.inputs
        sd = self.direction
        if sd == "OD" and not si[3].name[0] == "O":
            si[3].name = "Origin"
            si[4].name = "Direction"
            si[3].prop_name = 'v3_origin'
            si[4].prop_name = 'v3_dir'
        elif sd == "AB" and not si[3].name[0] == "A":
            si[3].name = "A"
            si[4].name = "B"
            si[3].prop_name = 'v3_input_0'
            si[4].prop_name = 'v3_input_1'

        ortho = sd not in ["AB", "OD"]
        if (not ortho and si[3].hide_safe) or ortho:
            si[3].hide_safe = ortho
            si[4].hide_safe = ortho

        updateNode(self, context)

    direction : EnumProperty(
        name="Direction", items=directionItems,
        default="X", update=update_vect_socket)

    num : IntProperty(
        name='Num Verts', description='Number of Vertices',
        default=2, min=2, update=updateNode)

    step : FloatProperty(
        name='Step', description='Step length',
        default=1.0, update=updateNode)

    center : BoolProperty(
        name='Center', description='Center the line',
        default=False, update=updateNode)

    normalize : BoolProperty(
        name='Normalize', description='Normalize line to size',
        default=False, update=update_size_socket)

    size : FloatProperty(
        name='Size', description='Size of line',
        default=10.0, update=updateNode)

    v3_input_0 : FloatVectorProperty(
        name='A', description='Starting point',
        size=3, default=(0, 0, 0),
        update=updateNode)

    v3_input_1 : FloatVectorProperty(
        name='B', description='End point',
        size=3, default=(0.5, 0.5, 0.5),
        update=updateNode)

    v3_origin : FloatVectorProperty(
        name='Origin', description='Origin of line',
        size=3, default=(0, 0, 0),
        update=updateNode)

    v3_dir : FloatVectorProperty(
        name='Direction', description='Direction',
        size=3, default=(1, 1, 1),
        update=updateNode)

    split: BoolProperty(name="Split to objects", description="Each object in separate object", update=updateNode)
    as_numpy: BoolProperty(name="Numpy output", description="Format of output data", update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Num").prop_name = 'num'
        self.inputs.new('SvStringsSocket', "Step").prop_name = 'step'
        self.inputs.new('SvStringsSocket', "Size").prop_name = 'size'
        self.inputs.new('SvVerticesSocket', "A").prop_name = 'v3_input_0'
        self.inputs.new('SvVerticesSocket', "B").prop_name = 'v3_input_1'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")

        self.inputs['Size'].hide_safe = True
        self.inputs["A"].hide_safe = True
        self.inputs["B"].hide_safe = True

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", toggle=True)
        row.prop(self, "normalize", toggle=True)

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'split')
        layout.prop(self, 'as_numpy')

    def rclick_menu(self, context, layout):
        layout.prop(self, 'split')
        layout.prop(self, 'as_numpy')

    def process(self):
        if not any(s.is_linked for s in self.outputs):
            return

        number, step, size, vas, vbs = [sock.sv_get() for sock in self.inputs]
        max_len = max([len(item) for item in [number, step, size, vas, vbs]])
        number = chain(number, cycle([number[-1]]))
        step = chain(step, cycle([step[-1]]))
        size = chain(size, cycle([size[-1]]))
        vas = chain(vas, cycle([vas[-1]]))
        vbs = chain(vbs, cycle([vbs[-1]]))
        out = []
        for i, n, st, si, va, vb in zip(range(max_len), number, step, size, vas, vbs):
            if self.direction in ['X', 'Y', 'Z']:
                out.append(make_line(n, st, si, self.direction, self.normalize, self.center))
            else:
                out.append(make_line_advanced(n, st, si, va, vb, self.direction, self.normalize, self.center))

        if self.split:
            verts, edges = zip(*out)
            verts_out, edges_out = [], []
            for vs, ns in zip(verts, edges):
                v_out, e_out = split_lines_to_objects(vs, ns)
                verts_out.extend(v_out)
                edges_out.extend(e_out)
        else:
            verts_out, edges_out = zip(*out)

        if not self.as_numpy:
            verts_out = [ar.tolist() for ar in verts_out]
            edges_out = [ar.tolist() for ar in edges_out]

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)


def register():
    bpy.utils.register_class(SvLineNodeMK3)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK3)
