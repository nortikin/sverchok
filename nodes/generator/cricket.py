# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
import bmesh

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.modules import sv_bmesh

class SvCricketNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: cricket
    Tooltip:  lowpoly cricket model
    
    """

    bl_idname = "SvCricketNode"
    bl_label = "Cricket"
    bl_icon = "GHOST_ENABLED"

    cricket_scale: bpy.props.FloatProperty(name='scale', default=4.0, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', "Scale").prop_name = "cricket_scale"
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket',  "Faces")

    def process(self):
        out_verts = []
        out_faces = []

        in_scale = self.inputs['Scale'].sv_get(default=[[self.cricket_scale]])
        
        verts, _, faces = sv_bmesh.create_cricket(as_pydata=True, scale=in_scale[0][0])
        out_verts.append(verts)
        out_faces.append(faces)

        self.outputs['Vertices'].sv_set(out_verts)
        self.outputs['Faces'].sv_set(out_faces)


classes = [SvCricketNode]
register, unregister = bpy.utils.register_classes_factory(classes)
