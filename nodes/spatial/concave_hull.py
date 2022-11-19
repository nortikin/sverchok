# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, ensure_nesting_level, zip_long_repeat, get_data_nesting_level
from sverchok.utils.alpha_shape import alpha_shape


class SvConcaveHullNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Concave Hull / Alpha Shape
    Tooltip: Calculate concave hull of a set of points by use of Alpha Shape algorithm
    """
    bl_idname = 'SvConcaveHullNode'
    bl_label = 'Concave Hull'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CONCAVE_HULL'
    sv_dependencies = {'scipy'}

    volume_threshold : FloatProperty(
        name = "PlanarThreshold",
        min = 0,
        default = 1e-4,
        precision = 4,
        update = updateNode)

    alpha : FloatProperty(
        name = "Alpha",
        min = 0,
        default = 2.0,
        description="Alpha value for the Alpha Shape algorithm. Bigger values correspond to bigger volume of the generated mesh. If the value is too small, the mesh can be non-manifold (have holes in it)",
        update = updateNode)

    normals : BoolProperty(
        name = "Correct normals",
        default = True,
        description="If checked, the node will recalculate the normals of generated mesh, so that they all point outside. Otherwise, the orientation of faces is not guaranteed",
        update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "normals")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Alpha").prop_name = 'alpha'
        self.inputs.new('SvStringsSocket', "PlanarThreshold").prop_name = 'volume_threshold'
        self.outputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvStringsSocket', "Edges")
        self.outputs.new('SvStringsSocket', "Faces")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        alpha_s = self.inputs['Alpha'].sv_get()
        volume_threshold_s = self.inputs['PlanarThreshold'].sv_get()

        input_level = get_data_nesting_level(vertices_s)

        vertices_s = ensure_nesting_level(vertices_s, 4)
        volume_threshold_s = ensure_nesting_level(volume_threshold_s, 2)
        alpha_s = ensure_nesting_level(alpha_s, 2)

        nested_output = input_level > 3

        verts_out = []
        edges_out = []
        faces_out = []
        for params in zip_long_repeat(vertices_s, alpha_s, volume_threshold_s):
            verts_item = []
            edges_item = []
            faces_item = []
            for vertices, alpha, volume_threshold in zip_long_repeat(*params):
                new_verts, new_edges, new_faces = alpha_shape(vertices, alpha, self.normals, volume_threshold)
                verts_item.append(new_verts)
                edges_item.append(new_edges)
                faces_item.append(new_faces)

            if nested_output:
                verts_out.append(verts_item)
                edges_out.append(edges_item)
                faces_out.append(faces_item)
            else:
                verts_out.extend(verts_item)
                edges_out.extend(edges_item)
                faces_out.extend(faces_item)

        self.outputs['Vertices'].sv_set(verts_out)
        self.outputs['Edges'].sv_set(edges_out)
        self.outputs['Faces'].sv_set(faces_out)


def register():
    bpy.utils.register_class(SvConcaveHullNode)


def unregister():
    bpy.utils.unregister_class(SvConcaveHullNode)
