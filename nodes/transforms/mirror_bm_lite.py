# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
import bmesh
from mathutils import Matrix, Vector

from bpy.props import FloatProperty, BoolProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, enum_item_4, match_long_repeat
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

    axis: EnumProperty(
        name="axis to mirror over", update=updateNode,
        default='X', items=enum_item_4(['X', 'Y', 'Z']))

    # mirror_u: BoolProperty(
    #     name="Mirror U", update=updateNode, description='')

    # mirror_v: BoolProperty(
    #     name="Mirror V", update=updateNode, description='')    

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
        layout.prop(self, "axis", expand=True)
        # row = layout.row(align=True)
        # row.prop(self, "mirror_u"); row.prop(self, "mirror_v")

    def compose_objects_from_inputs(self):
        objects = []

        if not self.inputs[0].is_linked:
            pass
        else:

            # right now vert/edge/face must be connected.. will fix asap
            vert_data = self.inputs[0].sv_get(default=[[]])
            edge_data = self.inputs[1].sv_get(default=[[]])
            face_data = self.inputs[2].sv_get(default=[[]])
            merge_data = self.inputs[3].sv_get(default=[[self.merge_distance]])
            matrix_data  = self.inputs[4].sv_get(default=[Matrix()])

            params = match_long_repeat([vert_data, edge_data, face_data])
            # print(params)
            for idx, geom in enumerate(zip(*params)):
                obj = lambda: None
                obj.geom = geom
                obj.merge_distance = merge_data[0][idx if idx < len(merge_data[0]) else -1]
                obj.matrix = matrix_data[idx if idx < len(matrix_data) else -1]
                objects.append(obj)

        return objects

    def process(self):
        
        vert_data_out, edge_data_out, face_data_out = [], [], []

        for idx, obj in enumerate(self.compose_objects_from_inputs()):

            bm = bmesh_from_pydata(*obj.geom)
            geom = (bm.verts[:] + bm.faces[:])

            extra_params = dict(axis=self.axis) #, mirror_u=self.mirror_u, mirror_v=self.mirror_v)
            bmesh.ops.mirror(bm, geom=geom, matrix=obj.matrix, merge_dist=obj.merge_distance, **extra_params)
            if self.recalc_normals:
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
            verts, edges, faces = pydata_from_bmesh(bm)
            bm.free()

            vert_data_out.append(verts)
            edge_data_out.append(edges)
            face_data_out.append(faces)

        self.outputs[0].sv_set(vert_data_out)
        self.outputs[1].sv_set(edge_data_out)
        self.outputs[2].sv_set(face_data_out)



classes = [SvMirrorLiteBMeshNode]
register, unregister = bpy.utils.register_classes_factory(classes)
