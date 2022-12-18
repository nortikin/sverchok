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
from bpy.props import BoolProperty, IntProperty,EnumProperty,FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode,match_long_repeat
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata

def bm_from_pydata(v,e,f,unchanged=True):
    'pydata to bmesh and Keep the index order of edges unchanged'
    bm = bmesh_from_pydata(v,e,f)
    if unchanged:
        for i,initial_edge in enumerate(e):
            now_edge = bm.edges.get((bm.verts[initial_edge[0]],bm.verts[initial_edge[1]]))
            now_edge.index = i
    return bm

class SvBMObjinputNode(SverchCustomTreeNode, bpy.types.Node):
    ''' BMesh In '''
    bl_idname = 'SvBMObjinputNode'
    bl_label = 'BMesh In'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_ALPHA' 

    def updata_mode(self,context):
        for key in self.inputs.keys():
            self.safe_socket_remove('inputs',key)
        
        if self.mode == 'POLYGON':
            self.inputs.new('SvVerticesSocket', 'Verts')
            self.inputs.new('SvStringsSocket', 'Edges')
            self.inputs.new('SvStringsSocket', 'Faces')
        elif self.mode == 'OBJECT':
            self.inputs.new('SvObjectSocket', 'Objects')
        else:
            pass
        updateNode(self, context)
    modes = [
            ('POLYGON', "polygon", "(verts,edges,face) to bmesh", 0),
            ('OBJECT', "object", "blender object to bmesh", 1),
            ('NEW', 'new bmesh', 'create an empty bmesh container',2)
        ]
    mode : EnumProperty(
        name = "Mode",
        description = "Method of converting to bmesh",
        items = modes,
        default = 'POLYGON',
        update = updata_mode)
    unchanged : BoolProperty(
        name = "Unchanged",
        description="Keep the index order of edges unchanged",
        default = True,
        update = updateNode)
    max: IntProperty(
        name= 'Max Number',
        description="""Maximum number of bmesh objects created,
        Prevent the creation of too many empty bmesh objects from causing Blender crash""",
        default= 5,
        update=updateNode)
    
    def draw_buttons(self, context, layout):
        layout.prop(self,'mode',text='')
        if self.mode == 'POLYGON':
            layout.prop(self,'unchanged')
        if self.mode == 'POLYGON' or self.mode == 'OBJECT':
            layout.prop(self,'max')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Verts')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.outputs.new('SvStringsSocket', 'Bmesh')
        
    def process(self):
        bmesh_list = []
        if self.mode == 'POLYGON':
            verts = self.inputs['Verts'].sv_get(default=[[]])
            edges = self.inputs['Edges'].sv_get(default=[[]])
            faces = self.inputs['Faces'].sv_get(default=[[]])
            for i,(v,e,f) in enumerate(zip(*match_long_repeat([verts,edges,faces]))):
                if i >= self.max:
                    break
                bm = bm_from_pydata(v,e,f,self.unchanged)
                bmesh_list.append(bm)
        elif self.mode == 'OBJECT':
            objs =  self.inputs['Objects'].sv_get(default=[])
            if not objs: 
                return
            for i,obj in enumerate(objs):
                if i >= self.max:
                    break
                bm = bmesh.new()
                bm.from_mesh(obj.data)
                bmesh_list.append(bm)
        else:
            bmesh_list.append(bmesh.new())
        self.outputs['Bmesh'].sv_set(bmesh_list)

def register():
    bpy.utils.register_class(SvBMObjinputNode)


def unregister():
    bpy.utils.unregister_class(SvBMObjinputNode)
