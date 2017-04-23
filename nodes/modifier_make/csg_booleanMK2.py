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
import bmesh
import sys

from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

from sverchok.utils.csg_core import CSG


def Boolean(VA, PA, VB, PB, operation):
    if not all([VA, PA, VB, PB]):
        return False, False

    a = CSG.Obj_from_pydata(VA, PA)
    b = CSG.Obj_from_pydata(VB, PB)

    faces = []
    vertices = []

    recursionlimit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)
    try:
        if operation == 'DIFF':
            polygons = a.subtract(b).toPolygons()
        elif operation == 'JOIN':
            polygons = a.union(b).toPolygons()
        elif operation == 'ITX':
            polygons = a.intersect(b).toPolygons()
    except RuntimeError as e:
        raise RuntimeError(e)

    sys.setrecursionlimit(recursionlimit)

    for polygon in polygons:
        indices = []
        for v in polygon.vertices:
            pos = [v.pos.x, v.pos.y, v.pos.z]
            if pos not in vertices:
                vertices.append(pos)
            index = vertices.index(pos)
            indices.append(index)

        faces.append(indices)

    return [[vertices], [faces]]


class SvCSGBooleanNode(bpy.types.Node, SverchCustomTreeNode):
    '''CSG Boolean Node'''
    bl_idname = 'SvCSGBooleanNode'
    bl_label = 'CSG Boolean'
    bl_icon = 'OUTLINER_OB_EMPTY'

    mode_options = [
        ("ITX", "Intersect", "", 0),
        ("JOIN", "Join", "", 1),
        ("DIFF", "Diff", "", 2)
    ]

    selected_mode = EnumProperty(
        items=mode_options,
        description="offers basic booleans using CSG",
        default="ITX",
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('VerticesSocket', 'Verts A')
        self.inputs.new('StringsSocket',  'Polys A')
        self.inputs.new('VerticesSocket', 'Verts B')
        self.inputs.new('StringsSocket',  'Polys B')
        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'Polygons', 'Polygons')

    def draw_buttons(self, context, layout):
        row = layout.row()
        row.prop(self, 'selected_mode', expand=True)

    def process(self):
        OutV, OutP = self.outputs
        if not OutV.is_linked:
            return
        VertA, PolA, VertB, PolB = self.inputs
        SMode = self.selected_mode
        out = []
        VA = VertA.sv_get()
        PA = PolA.sv_get()
        VB = VertB.sv_get()
        PB = PolB.sv_get()
        for v1, p1, v2, p2 in zip(VA, PA, VB, PB):
            out.append(Boolean(v1, p1, v2, p2, SMode))
        OutV.sv_set([i[0] for i in out])
        if OutP.is_linked:
            OutP.sv_set([i[1] for i in out])


def register():
    bpy.utils.register_class(SvCSGBooleanNode)


def unregister():
    bpy.utils.unregister_class(SvCSGBooleanNode)
