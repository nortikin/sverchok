# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.sv_bmesh_utils import bmesh_from_pydata
from sverchok.utils.field.rbf import mesh_field
from sverchok.dependencies import scipy
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.utils.math import rbf_functions

if scipy is None:
    add_dummy('SvMeshSurfaceFieldNode', "Mesh Smoothed Surface Field", 'scipy')

class SvMeshSurfaceFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Mesh Surface Field
    Tooltip: Generate scalar field, defining a smoothed surface of the mesh
    """
    bl_idname = 'SvMeshSurfaceFieldNode'
    bl_label = 'Mesh Smoothed Surface Field'
    bl_icon = 'OUTLINER_OB_EMPTY'

    function : EnumProperty(
            name = "Function",
            items = rbf_functions,
            default = 'multiquadric',
            update = updateNode)

    epsilon : FloatProperty(
            name = "Epsilon",
            default = 1.0,
            min = 0.0,
            update = updateNode)
    
    scale : FloatProperty(
            name = "Scale",
            default = 1.0,
            update = updateNode)
    
    smooth : FloatProperty(
            name = "Smooth",
            default = 0.0,
            min = 0.0,
            update = updateNode)

    use_verts : BoolProperty(
            name = "Use Vertices",
            default = True,
            update = updateNode)

    use_edges : BoolProperty(
            name = "Use Edges",
            default = False,
            update = updateNode)

    use_faces : BoolProperty(
            name = "Use Faces",
            default = False,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "function")
        layout.prop(self, "use_verts")
        layout.prop(self, "use_edges")
        layout.prop(self, "use_faces")

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', 'Vertices')
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', "Epsilon").prop_name = 'epsilon'
        self.inputs.new('SvStringsSocket', "Smooth").prop_name = 'smooth'
        self.inputs.new('SvStringsSocket', "Scale").prop_name = 'scale'
        self.outputs.new('SvScalarFieldSocket', "Field")

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()
        edges_s = self.inputs['Edges'].sv_get()
        faces_s = self.inputs['Faces'].sv_get()
        epsilon_s = self.inputs['Epsilon'].sv_get()
        smooth_s = self.inputs['Smooth'].sv_get()
        scale_s = self.inputs['Scale'].sv_get()

        input_level = get_data_nesting_level(vertices_s)
        vertices_s = ensure_nesting_level(vertices_s, 4)
        edges_s = ensure_nesting_level(edges_s, 4)
        faces_s = ensure_nesting_level(faces_s, 4)
        epsilon_s = ensure_nesting_level(epsilon_s, 2)
        smooth_s = ensure_nesting_level(smooth_s, 2)
        scale_s = ensure_nesting_level(scale_s, 2)

        nested_output = input_level > 3

        fields_out = []
        for params in zip_long_repeat(vertices_s, edges_s, faces_s, epsilon_s, smooth_s, scale_s):
            new_fields = []
            for vertices, edges, faces, epsilon, smooth, scale in zip_long_repeat(*params):
                bm = bmesh_from_pydata(vertices, edges, faces, normal_update=True)
                field = mesh_field(bm, self.function, smooth, epsilon, scale,
                            use_verts = self.use_verts,
                            use_edges = self.use_edges,
                            use_faces = self.use_faces)
                new_fields.append(field)
            if nested_output:
                fields_out.append(new_fields)
            else:
                fields_out.extend(new_fields)

        self.outputs['Field'].sv_set(fields_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvMeshSurfaceFieldNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvMeshSurfaceFieldNode)

