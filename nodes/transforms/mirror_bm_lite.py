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

axis_dict = {'X': (1, 0, 0), 'Y': (0, 1, 0), 'Z': (0, 0, 1)} 


class SvMirrorLiteBMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: mirror lite
    Tooltip:  a basic mirror using bmesh.ops.mirror
    
    """

    bl_idname = 'SvMirrorLiteBMeshNode'
    bl_label = 'Mirror Lite (bm.ops)'
    bl_icon = 'GREASEPENCIL'

    bisect_first: BoolProperty(
        update=updateNode, name='bisect first',
        description='drop geometry outside of the mirror axis, bisect the overlapping geometry')

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
        # self.inputs.new('SvMatrixSocket', "Mirror Matrix").hide = True

        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def draw_buttons(self, context, layout):
        layout.prop(self, "recalc_normals", toggle=True)
        layout.prop(self, "axis", expand=True)
        layout.prop(self, "bisect_first", expand=True)
        # row = layout.row(align=True)
        # row.prop(self, "mirror_u"); row.prop(self, "mirror_v")
    
    #def rclick_menu(self, context, layout):
    #    if "Mirror Matrix" in self.inputs:
    #        layout.prop(self.inputs["Mirror Matrix"], 'hide', text="Matrix Socket (optional)")

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
            # matrix_data  = self.inputs[4].sv_get(default=[Matrix()])

            params = match_long_repeat([vert_data, edge_data, face_data])
            for idx, geom in enumerate(zip(*params)):
                obj = lambda: None
                obj.geom = geom
                obj.merge_distance = merge_data[0][idx if idx < len(merge_data[0]) else -1]
                obj.matrix = Matrix() # matrix_data[idx if idx < len(matrix_data) else -1]
                objects.append(obj)

        return objects

    def process(self):
        
        vert_data_out, edge_data_out, face_data_out = [], [], []

        for idx, obj in enumerate(self.compose_objects_from_inputs()):

            bm = bmesh_from_pydata(*obj.geom, normal_update=True)

            # # bisect over the axis and obj.matrix first.
            # if self.bisect_first:
            #     bisect_geom = (bm.verts[:] + bm.edges[:] + bm.faces[:])
            #     pp = obj.matrix.to_translation()
            #     axis_tuple = axis_dict[self.axis]
            #     pno = Vector(axis_tuple) @ obj.matrix.to_3x3().transposed()
            #     res = bmesh.ops.bisect_plane(
            #         bm, geom=bisect_geom, dist=0.00001, plane_co=pp, plane_no=pno, 
            #         use_snap_center=False, clear_outer=False, clear_inner=True)

            # geom = (bm.verts[:] + bm.edges[:] + bm.faces[:])
            # extra_params = dict(axis=self.axis) #, mirror_u=self.mirror_u, mirror_v=self.mirror_v)
            # bmesh.ops.mirror(bm, geom=geom, matrix=obj.matrix, merge_dist=obj.merge_distance, **extra_params)
            
            geom = (bm.verts[:] + bm.edges[:] + bm.faces[:])
            bmesh.ops.symmetrize(bm, input=geom, direction=self.axis, dist=obj.merge_distance)

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
