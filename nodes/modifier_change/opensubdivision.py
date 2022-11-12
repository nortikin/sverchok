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

# Implements the Catmull-Clark Subdivision Node 
# sverchok/nodes/modifier_change/opensubdivision.py

import bpy
from bpy.props import IntProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat

enable_module = False
try:
    import pyOpenSubdiv
    from pyOpenSubdiv.pysubdivision import pysubdivide    
    enable_module = True
except ModuleNotFoundError:
    enable_module = False

from itertools import chain 
import traceback 
class SvOpenSubdivisionNode(bpy.types.Node,SverchCustomTreeNode):
    bl_idname = "SvOpenSubdivisionNode" # Use this for index.md reference 
    bl_label = "Catmull-Clark Subdivision"
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = None 

    maxSubdivision = 6 # creates a self.maxSubdivision attribute 

    # Mute Node Implementation 
    @property
    def sv_internal_links(self):
        mapping =  [
            (self.inputs['Vertices'],self.outputs['Vertices']),
            (self.inputs['Faces'],self.outputs['Faces'])
        ]        
        return mapping 

    def sv_init(self,context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")

        socket = self.inputs.new('SvStringsSocket', "Levels")
        socket.use_prop=True
        socket.default_property_type = 'int'
        socket.default_int_property = 0
        # socket.int_range = (0,self.maxSubdivision) # There's no way to visually limit the subdivision levels (it's handled internally), but something like this would be nice in the future. 

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not enable_module:
            raise Exception("The dependent library is not installed (pyOpenSubdiv).")

        vert_sets = self.inputs['Vertices'].sv_get(default=[],deepcopy=False)
        edges = []         
        face_sets = self.inputs['Faces'].sv_get(default=[],deepcopy=False)
        
        new_meshes = {
            'vertices':[],            
            'edges':[],
            'faces':[]
        }
        
        if(vert_sets != [] and face_sets != []):
            subdivision_levels = self.inputs["Levels"].sv_get()[0]

            # This is definitely gonna crash. 
            # I think I'll take the "wait and see how" approach?
            parameters = zip(*match_long_repeat([subdivision_levels,vert_sets,face_sets]))
            
            for params in parameters:
                subdivision_level = params[0] if params[0] <= self.maxSubdivision else self.maxSubdivision
                vertices = params[1]
                faces = params[2] 
                faceVerts = list(chain.from_iterable(faces))
                vertsPerFace = [len(face) for face in faces]

                new_mesh = pysubdivide(subdivision_level,
                vertices,
                faces,
                faceVerts,
                vertsPerFace,
                verbose = False
                )
                
                new_meshes['vertices'].append(new_mesh['vertices'])
                new_meshes['edges'].append(new_mesh['edges'])
                new_meshes['faces'].append(new_mesh['faces'])

        self.outputs['Vertices'].sv_set(new_meshes['vertices'])
        self.outputs['Edges'].sv_set(new_meshes['edges'])
        self.outputs['Faces'].sv_set(new_meshes['faces'])

def register():    
    bpy.utils.register_class(SvOpenSubdivisionNode)

def unregister():
    bpy.utils.unregister_class(SvOpenSubdivisionNode)
