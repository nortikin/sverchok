# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh
from mathutils import Matrix, Vector

from bpy.props import FloatProperty, BoolProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata, pydata_from_bmesh

class SvMirrorLiteBMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: mirror lite
    Tooltip:  a basic mirror using bmesh.ops.mirror
    
    """

    bl_idname = 'SvMirrorLiteBMeshNode'
    bl_label = 'Mirror Lite (bm.ops)'
    bl_icon = 'GREASEPENCIL'

    recalc_normals: BoolProperty(
        name='recalc face normals', default=True, update=updateNode, 
        description='mirror will invert faces, this will correct that, usually..')
    
    merge_distance: FloatProperty(
        name='merge distance', default=0.0, update=updateNode,
        description='distance over which the mirror will join two meshes')

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Edges")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvStringsSocket', "Merge Distance").prop_name = 'merge_distance'
        self.inputs.new('SvMatrixSocket', "Mirror Matrix")

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "recalc_normals", toggle=True)

    def compose_objects_from_inputs(self):
        if not self.inputs[0].is_linked:
            objects = []
        else:
            objects = []
            # for .. in sockets:
            #     verts =
            #     edges =
            #     faces =
            #     obj = lambda: None
            #     obj.geom = verts, edges, faces
            #     obj.merge_distance = ...
            #     obj.matrix = yield self.inputs['Plane'].sv_get(default=[Matrix()])
            #     objects.append(obj)
        return objects

    def process(self):
        
        for idx, obj in enumerate(self.compose_objects_from_inputs()):

            bm = bmesh_from_pydata(*obj.geom)
            # all parans:   (bm, geom=[], matrix=Matrix(), merge_dist=0.0, axis='X', mirror_u=False, mirror_v=False)
            bmesh.ops.mirror(bm, geom=(bm.verts[:] + bm.faces[:]), matrix=obj.matrix, merge_dist=obj.merge_distance, axis='X')
            if self.recalc_normals:
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            verts, edges, faces = pydata_from_bmesh(bm)
            bm.free()


classes = [SvMirrorLiteBMeshNode]
register, unregister = bpy.utils.register_classes_factory(classes)
