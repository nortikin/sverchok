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
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

from sverchok.utils.modules.ctypes_pyOpenSubdiv import pyOpenSubdiv
openSubdivide = pyOpenSubdiv

from itertools import chain 
import traceback 
class SvOpenSubdivideNode(bpy.types.Node,SverchCustomTreeNode):
    bl_idname = "SvOpenSubdivideNode"
    bl_label = "OpenSubdiv"
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = None 

    maxlevel : IntProperty(name='level',default=0,min=0,max=5,update=updateNode)

    def sv_init(self,context):
        self.inputs.new('SvStringsSocket', "Levels").prop_name='maxlevel'
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        vert_sets = self.inputs['Vertices'].sv_get(default=[],deepcopy=False)
        edges = []         
        face_sets = self.inputs['Faces'].sv_get(default=[],deepcopy=False)
        
        
        if(vert_sets != [] and face_sets != []):
            subdivision_levels = self.inputs["Levels"].sv_get()[0]

            # This is definitely gonna crash. 
            # I think I'll take the "wait and see how" approach?
            parameters = zip(*match_long_repeat([subdivision_levels,vert_sets,face_sets]))

            new_meshes = {
                'vertices':[],
                'edges':[],
                'faces':[]
            }
            
            for params in parameters:
                subdivision_level = params[0]                
                vertices = params[1]
                faces = params[2] 
                faceVerts = list(chain.from_iterable(faces))
                vertsPerFace = [len(face) for face in faces]

                new_mesh = openSubdivide(subdivision_level,vertices,faceVerts,vertsPerFace)
                if(implementation['Boost']):
                    new_meshes['vertices'].append(new_mesh['verts']) # Boost implementation 
                    new_meshes['edges'].append(new_mesh['edges'])
                    new_meshes['faces'].append(new_mesh['faces'])
                elif(implementation['ctypes']):
                    new_meshes['vertices'].append(new_mesh['vertices']) # ctypes implementation 
                    new_meshes['edges'].append(new_mesh['edges'])
                    new_meshes['faces'].append(new_mesh['faces'])

            self.outputs['Vertices'].sv_set(new_meshes['vertices'])
            self.outputs['Edges'].sv_set(new_meshes['edges'])
            self.outputs['Faces'].sv_set(new_meshes['faces'])
        
        else:
            self.outputs['Vertices'].sv_set(vertices)
            self.outputs['Edges'].sv_set(edges)
            self.outputs['Faces'].sv_set(faces)
        

def register():
    bpy.utils.register_class(SvOpenSubdivideNode)

def unregister():
    bpy.utils.unregister_class(SvOpenSubdivideNode)



