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

import bpy
import mathutils

from bpy.props import IntProperty, FloatProperty, FloatVectorProperty
from mathutils.geometry import interpolate_bezier as bezlerp
from mathutils import Vector

from sv_node_tree import SverchCustomTreeNode, VerticesSocket, StringsSocket
from sv_data_structure import (updateNode, fullList,
                            SvSetSocketAnyType, SvGetSocketAnyType)


def generate_bezier(verts=[], num_verts=20):

    f = list(map(Vector, verts))
    knot1, ctrl_1, ctrl_2, knot2 = f
    arc_verts = bezlerp(knot1, ctrl_1, ctrl_2, knot2, max(3, num_verts))

    arc_verts = [v[:] for v in arc_verts]
    arc_edges = [(n, n+1) for n in range(len(arc_verts)-1)]
    return arc_verts, arc_edges


class BasicSplineNode(bpy.types.Node, SverchCustomTreeNode):
    ''' Line '''
    bl_idname = 'BasicSplineNode'
    bl_label = 'BasicSpline'
    bl_icon = 'OUTLINER_OB_EMPTY'

    num_verts = IntProperty(
        name='num_verts',
        description='Num Vertices',
        default=10, min=3,
        update=updateNode)

    knot_1 = FloatVectorProperty(name='knot_1', description="k1", update=updateNode)
    ctrl_1 = FloatVectorProperty(name='ctrl_1', description="ctrl1", update=updateNode)
    ctrl_2 = FloatVectorProperty(name='ctrl_2', description="ctrl2", update=updateNode)
    knot_2 = FloatVectorProperty(name='knot_2', description="k2", update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "num_verts").prop_name = 'num_verts'

        self.inputs.new('VerticesSocket', "knot_1").prop_name = 'knot_1'
        self.inputs.new('VerticesSocket', "ctrl_1").prop_name = 'ctrl_1'
        self.inputs.new('VerticesSocket', "ctrl_2").prop_name = 'ctrl_2'
        self.inputs.new('VerticesSocket', "knot_2").prop_name = 'knot_2'

        self.outputs.new('VerticesSocket', "Verts", "Verts")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('VerticesSocket', "hnd Verts", "hnd Verts")
        self.outputs.new('StringsSocket', "hnd Edges", "hnd Edges")

    def draw_buttons(self, context, layout):
        pass

    def update(self):
        outputs = self.outputs

        '''
        - is hnd_edges socket created, means all sockets exist.
        - is anything connected to the Verts socket?
        '''
        if not (('hnd Edges' in outputs) and (outputs['Verts'].links)):
            return

        '''
        operational scheme: (spline = handle set (k1, ctrl1, ctrl2, k2))

        - num_vert can be given per spline
        - if no num_vert is given, default is used for all splines
        - if node receives more splines than items in num_vert list, last is re-used.
        - each (k1 ctrl1 ctrl2 k2) must have input
        - the length of (k1 ctrl1 ctrl2 k2) individually must be equal (no last used)
        '''

        inputs = self.inputs
        handle_names = ['knot_1', 'ctrl_1', 'ctrl_2', 'knot_2']

        if not all([inputs[p].links for p in handle_names]):
            return

        # assume they all match, reduce cycles used for checking.
        handle_sockets = (inputs[handle_names[i]] for i in range(4))
        handle_data = []
        for socket in handle_sockets:
            v = []
            if isinstance(socket.links[0].from_socket, VerticesSocket):
                v = SvGetSocketAnyType(self, socket, deepcopy=False)[0]
            handle_data.append(v)

        knots_1, ctrls_1, ctrls_2, knots_2 = handle_data
        if not (len(knots_1) == len(ctrls_1) == len(ctrls_2) == len(knots_2)):
            return

        # get vert_nums, or pad till matching quantity
        nv = []
        nv_links = inputs['num_verts'].links
        if nv_links:
            if isinstance(nv_links[0].from_socket, StringsSocket):
                nv = SvGetSocketAnyType(self, inputs['num_verts'], deepcopy=False)[0]

            if nv and (len(nv) < len(knots_1)):
                pad_num = len(knots_1) - len(nv)
                for i in range(pad_num):
                    nv.append(nv[-1])
        else:
            for i in range(len(knots_1)):
                nv.append(self.num_verts)

        # iterate over them
        verts_out = []
        edges_out = []
        h_verts_out = []
        h_edges_out = []
        for idx, handle_set in enumerate(zip(knots_1, ctrls_1, ctrls_2, knots_2)):

            divisions = nv[idx] if idx < len(nv) else 3

            v, e = generate_bezier(handle_set, divisions)
            verts_out.append(v)
            edges_out.append(e)

            # for visual
            h_verts_out.append(handle_set)
            h_edges_out.append([(0, 1), (2, 3)])

        # reaches here if we got usable data.
        SvSetSocketAnyType(self, 'Verts', verts_out)
        if outputs['Edges'].links:
            SvSetSocketAnyType(self, 'Edges', edges_out)

        # optional, show handles. this is useful for visual debug.
        if outputs['hnd Verts'].links:
            SvSetSocketAnyType(self, 'hnd Verts', h_verts_out)

            if outputs['hnd Edges'].links:
                SvSetSocketAnyType(self, 'hnd Edges', h_edges_out)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(BasicSplineNode)


def unregister():
    bpy.utils.unregister_class(BasicSplineNode)
