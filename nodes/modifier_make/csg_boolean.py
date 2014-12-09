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

from bpy.props import FloatProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

from sverchok.utils.csg_core import CSG
from sverchok.utils.csg_geom import Vertex, Vector   # these may prove redundant.


def Boolean(VA, PA, VB, PB, boolean_mode):
    if not all([VA, PA, VB, PB]):
        return False, False

    # bmA = bmesh_from_pydata(VA, [], PA)  
    # bmB = bmesh_from_pydata(VB, [], PB)
    # magic.
    #
    #
    # verts_out, faces_out = some operation
    #
    #
    #
    # bmA.clear()
    # bmA.free()
    # bmB.clear()
    # bmB.free()

    '''
    self.faces = []
    self.normals = []
    self.vertices = []
    self.vnormals = []
    self.list = -1
    
    a = CSG.cube()
    b = CSG.cylinder(radius=0.5, start=[0., -2., 0.], end=[0., 2., 0.])
        
    recursionlimit = sys.getrecursionlimit()
    sys.setrecursionlimit(10000)
    try:
        if operation == 'subtract':
            polygons = a.subtract(b).toPolygons()
        elif operation == 'union':
            polygons = a.union(b).toPolygons()
        elif operation == 'intersect':
            polygons = a.intersect(b).toPolygons()
    except RuntimeError as e:
        raise RuntimeError(e)

    sys.setrecursionlimit(recursionlimit)
    
    for polygon in polygons:
        n = polygon.plane.normal
        indices = []
        for v in polygon.vertices:
            pos = [v.pos.x, v.pos.y, v.pos.z]
            if not pos in self.vertices:
                self.vertices.append(pos)
                self.vnormals.append([])
            index = self.vertices.index(pos)
            indices.append(index)
            self.vnormals[index].append(v.normal)
        self.faces.append(indices)
        self.normals.append([n.x, n.y, n.z])
    
    # setup vertex-normals
    ns = []
    for vns in self.vnormals:
        n = Vector(0.0, 0.0, 0.0)
        for vn in vns:
            n = n.plus(vn)
        n = n.dividedBy(len(vns))
        ns.append([a for a in n])
    self.vnormals = ns
    '''

    return (verts_out, faces_out)


class SvCSGBooleanNode(bpy.types.Node, SverchCustomTreeNode):
    '''CSG Boolean Node'''
    bl_idname = 'SvCSGBooleanNode'
    bl_label = 'CSG BooleanNode'
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
        # draw operation type enum
        row.prop(self, 'selected_mode', expand=True)
        pass

    def process(self):
        for i in range(4):
            if not self.inputs[i].is_linked:
                return

        if not self.outputs['Vertices'].is_linked:
            return

        VA = self.inputs['Verts A'].sv_get()
        PA = self.inputs['Polys A'].sv_get()
        VB = self.inputs['Verts B'].sv_get()
        PB = self.inputs['Polys B'].sv_get()

        verts_out, polys_out = Boolean(VA, BA, VB, PB, selected_mode)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Polygons'].sv_set(polys_out)


def register():
    bpy.utils.register_class(SvCSGBooleanNode)


def unregister():
    bpy.utils.unregister_class(SvCSGBooleanNode)
