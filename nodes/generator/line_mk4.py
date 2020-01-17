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

from collections import namedtuple
from itertools import chain, cycle
import numpy as np

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


Directions = namedtuple('Directions', ['x', 'y', 'z', 'op', 'od'])
DIRECTION = Directions('X', 'Y', 'Z', 'OP', 'OD')
direction_items = [
    (DIRECTION.x,  DIRECTION.x,  "Along X axis",         0),
    (DIRECTION.y,  DIRECTION.y,  "Along Y axis",         1),
    (DIRECTION.z,  DIRECTION.z,  "Along Z axis",         2),
    (DIRECTION.op, DIRECTION.op, "Origin and point on line", 3),
    (DIRECTION.od, DIRECTION.od, "Origin and Direction", 4),
    ]

Lengths = namedtuple('Lengths', ['size', 'number', 'step'])
LENGTH = Lengths('Size', 'Number', 'Step')
length_items = [(i, i, '') for i in LENGTH]


def make_line(numbers=None, steps=None, sizes=None, verts_or=None, verts_dir=None,
              dir_mode=DIRECTION.x, size_mode=LENGTH.size, center=False):
    """
    Generate lines
    :param numbers: list of values, number of generated vertices
    :param steps: list of values, distance between points for step mode only
    :param sizes: list of values, length of a line for size mode only
    :param verts_or: list of tuple(float, float, float), custom origin of a line
    :param verts_dir: list of tuple(float, float, float), custom direction of a line
    :param dir_mode: 'X', 'Y', 'Z', 'OP' or 'OD', 'OP' and 'OD' mode for custom origin and direction
    :param size_mode: 'Size' or 'Step', length of line
    :param center: if True center of a line is moved to origin
    :return: np.array of vertices, np.array of edges
    """
    line_number = max(len(numbers), len(sizes), len(steps), len(verts_or), len(verts_dir))
    vert_number = sum([v_number if v_number > 1 else 2 for _, v_number in
                             zip(range(line_number), chain(numbers, cycle([numbers[-1]])))])
    numbers = cycle([None]) if numbers is None else chain(numbers, cycle([numbers[-1]]))
    steps = cycle([None]) if steps is None else chain(steps, cycle([steps[-1]]))
    sizes = cycle([None]) if sizes is None else chain(sizes, cycle([sizes[-1]]))
    verts_or = cycle([None]) if verts_or is None else chain(verts_or, cycle([verts_or[-1]]))
    verts_dir = cycle([None]) if verts_dir is None else chain(verts_dir, cycle([verts_dir[-1]]))
    verts_lines = np.empty((vert_number, 3))
    edges_lines = []
    num_added_verts = 0
    indexes = iter(range(int(1e+100)))

    for i_line, n, st, size, vor, vdir in zip(range(line_number), numbers, steps, sizes, verts_or, verts_dir):
        vor, vdir = get_corner_points(dir_mode, center, vor, vdir, get_len_line(size_mode, n, size, st))
        line_verts = generate_verts(vor, vdir, n)
        edges_lines.extend([(i, i + 1) for i, _ in zip(indexes, line_verts[:-1])])
        verts_lines[num_added_verts: num_added_verts + len(line_verts)] = line_verts
        num_added_verts += len(line_verts)
    return verts_lines, edges_lines


def get_len_line(len_mode, number, size, step):
    # returns length of line according logic of a mode
    if len_mode == LENGTH.size:
        return size
    elif len_mode == LENGTH.number:
        return (number - 1 if number > 2 else 1) * step


def get_corner_points(dir_mode=DIRECTION.x, center=False, vert_a=None, vert_b=None, len_line=None):
    # returns coordinates of firs and last points of live according properties of the node
    directions = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
    origin = np.array(vert_a) if dir_mode in (DIRECTION.op, DIRECTION.od) else np.array((0, 0, 0))
    if dir_mode == DIRECTION.op:
        direction = np.array(vert_b) - origin
    elif dir_mode == DIRECTION.od:
        direction = np.array(vert_b)
    else:
        direction = np.array(directions[dir_mode])
    norm_dir = direction / np.linalg.norm(direction)
    if center:
        origin = origin - norm_dir * (len_line / 2)
    return origin, norm_dir * len_line + origin


def make_line_multiple_steps(steps, verts_a=None, verts_b=None, dir_mode=DIRECTION.x, center=False):
    """
    Generate lines between two given points in 'AB' mode or determined by origin(vert_a) and direction(vert_b)
    :param steps: list of values, each step is nest segment of a same line
    :param verts_a: list of tuple(float, float, float), origin of a line, only for 'OD' mode
    :param verts_b: list of tuple(float, float, float), direction of a line, only for 'OD' mode
    :param dir_mode: 'X', 'Y', 'Z', 'OP' or 'OD', 'OP' and 'OD' mode for custom origin and direction
    :param center: if True center of a line is moved to origin
    :return: numpy array with shape(number of vertices, 3), list of tuple(int, int)
    """
    line_number = max(len(verts_a or 1), len(verts_b or 1))
    vert_number = line_number * (len(steps) + 1)
    len_line = sum(steps)
    accum_steps = np.add.accumulate(steps)
    verts_a = cycle([None]) if verts_a is None else chain(verts_a, cycle([verts_a[-1]]))
    verts_b = cycle([None]) if verts_b is None else chain(verts_b, cycle([verts_b[-1]]))
    accum_steps = cycle([accum_steps])
    verts_lines = np.empty((vert_number, 3))
    edges_lines = []
    num_added_verts = 0
    indexes = iter(range(int(1e+100)))

    for line_i, sts, va, vb in zip(range(line_number), accum_steps, verts_a, verts_b):
        directions = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)}
        origin = np.array(va) if dir_mode in (DIRECTION.op, DIRECTION.od) else np.array((0, 0, 0))
        if dir_mode == DIRECTION.op:
            direction = np.array(vb) - origin
        elif dir_mode == DIRECTION.od:
            direction = np.array(vb)
        else:
            direction = np.array(directions[dir_mode])
        norm_dir = direction / np.linalg.norm(direction)
        if center:
            origin = origin - norm_dir * (len_line / 2)
        line_verts = np.full((len(steps), 3), norm_dir)
        line_verts = line_verts * sts.reshape((len(steps), 1))
        line_verts = line_verts + origin

        edges_lines.extend([(i, i + 1) for i, _ in zip(indexes, line_verts)])
        verts_lines[num_added_verts] = origin
        verts_lines[num_added_verts + 1: num_added_verts + len(line_verts) + 1] = line_verts
        num_added_verts += len(line_verts) + 1
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


class SvLineNodeMK4(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Line, segment.
    Tooltip: Generate line.
    """
    bl_idname = 'SvLineNodeMK4'
    bl_label = 'Line'
    bl_icon = 'GRIP'
    sv_icon = 'SV_LINE'

    def update_sockets(self, context):
        """ need to do UX transformation before updating node"""
        def set_hide(sock, status):
            if sock.hide_safe != status:
                sock.hide_safe = status

        if self.direction in (DIRECTION.op, DIRECTION.od):
            set_hide(self.inputs['Origin'], False)
            set_hide(self.inputs['Direction'], False)
        else:
            set_hide(self.inputs['Origin'], True)
            set_hide(self.inputs['Direction'], True)

        if self.length_mode == LENGTH.size:
            set_hide(self.inputs['Num'], False)
            set_hide(self.inputs['Steps'], True)
            set_hide(self.inputs['Size'], False)
            self.inputs['Steps'].prop_name = 'step'
        elif self.length_mode == LENGTH.number:
            set_hide(self.inputs['Num'], False)
            set_hide(self.inputs['Steps'], False)
            set_hide(self.inputs['Size'], True)
            self.inputs['Steps'].prop_name = 'step'
        elif self.length_mode == LENGTH.step:
            set_hide(self.inputs['Num'], True)
            set_hide(self.inputs['Steps'], False)
            set_hide(self.inputs['Size'], True)
            self.inputs['Steps'].prop_name = ''

        updateNode(self, context)

    direction: EnumProperty(name="Direction", items=direction_items, default="X", update=update_sockets)
    num: IntProperty(name='Num Verts', description='Number of Vertices', default=2, min=2, update=updateNode)
    step: FloatProperty(name='Step', description='Step length', default=1.0, update=updateNode)
    center: BoolProperty(name='Center', description='Center the line', default=False, update=updateNode)
    size: FloatProperty(name='Size', description='Size of line', default=10.0, update=updateNode)
    split: BoolProperty(name="Split to objects", description="Each object in separate object", default=True, 
                        update=updateNode)
    as_numpy: BoolProperty(name="Numpy output", description="Format of output data", update=updateNode)
    length_mode: EnumProperty(items=length_items, update=update_sockets)
    v3_dir: FloatVectorProperty(name='Direction', description='Direction', size=3, default=(1, 1, 1), update=updateNode)
    v3_origin: FloatVectorProperty(name='Origin', description='Origin of line', size=3, default=(0, 0, 0),
                                   update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Num").prop_name = 'num'
        self.inputs.new('SvStringsSocket', "Steps").prop_name = 'step'
        self.inputs.new('SvStringsSocket', "Size").prop_name = 'size'
        self.inputs.new('SvVerticesSocket', "Origin").prop_name = 'v3_origin'
        self.inputs.new('SvVerticesSocket', "Direction").prop_name = 'v3_dir'
        self.outputs.new('SvVerticesSocket', "Verts")
        self.outputs.new('SvStringsSocket', "Edges")

        self.inputs['Steps'].hide_safe = True
        self.inputs["Origin"].hide_safe = True
        self.inputs["Direction"].hide_safe = True

    def draw_buttons(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "length_mode", expand=True)
        row = col.row(align=True)
        row.prop(self, "center", text="Center to origin")

    def draw_buttons_ext(self, context, layout):
        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "direction", expand=True)
        row = col.row(align=True)
        row.prop(self, "length_mode", expand=True)
        layout.prop(self, "center", text="Center to origin")
        layout.prop(self, 'split')
        layout.prop(self, 'as_numpy')

    def rclick_menu(self, context, layout):
        layout.prop(self, 'split')
        layout.prop(self, 'as_numpy')

    def process(self):
        if self.length_mode == LENGTH.step and not self.inputs['Steps'].is_linked:
            return

        number, step, size, ors, dirs = [sock.sv_get(deepcopy=False) for sock in self.inputs]
        num_objects = max([len(item) for item in [number, step, size, ors, dirs]])
        number = chain(number, cycle([number[-1]]))
        step = chain(step, cycle([step[-1]]))
        size = chain(size, cycle([size[-1]]))
        ors = chain(ors, cycle([ors[-1]]))
        dirs = chain(dirs, cycle([dirs[-1]]))
        out = []
        for i, n, st, si, va, d in zip(range(num_objects), number, step, size, ors, dirs):
            if self.length_mode == LENGTH.step:
                out.append(make_line_multiple_steps(st, va, d, self.direction, self.center))
            else:
                out.append(make_line(n, st, si, va, d, self.direction, self.length_mode, self.center))
        if self.split:
            temp = [split_lines_to_objects(*data) for data in out]
            out = [v for res in temp for v in zip(*res)]
        if not self.as_numpy:
            out = [(ar.tolist(), edges) for ar, edges in out]
        [sock.sv_set(data) for sock, data in zip(self.outputs, zip(*out))]


def register():
    bpy.utils.register_class(SvLineNodeMK4)


def unregister():
    bpy.utils.unregister_class(SvLineNodeMK4)
