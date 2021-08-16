# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, get_data_nesting_level, ensure_nesting_level
from sverchok.utils.relax_mesh import *

class SvRelaxMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Relax Mesh
    Tooltip: Relax mesh
    """
    bl_idname = 'SvRelaxMeshNode'
    bl_label = 'Relax Mesh'
    bl_icon = 'MOD_SMOOTH'

    iterations: IntProperty(
        name="Iterations",
        min=0,
        max=1000, default=1, update=updateNode)

    factor: FloatProperty(
        name="Factor",
        description="Smoothing factor",
        min=0.0,
        max=1.0,
        default=0.5,
        update=updateNode)

    def update_sockets(self, context):
        self.inputs['Factor'].hide_safe = self.algorithm not in {'EDGES', 'FACES'}
        updateNode(self, context)

    algorithms = [
            ('LLOYD', "Lloyd", "Lloyd", 0),
            ('EDGES', "Edge Lengths", "Try to make all edges of the same length", 1),
            ('FACES', "Face Areas", "Try to make all faces of the same area", 2)
        ]

    algorithm : EnumProperty(
            name = "Algorithm",
            items = algorithms,
            default = 'LLOYD',
            update = update_sockets)

    def get_available_methods(self, context):
        items = []
        items.append((NONE, "Do not use", "Do not use", 0))
        if self.algorithm == 'LLOYD':
            items.append((LINEAR, "Linear", "Linear", 1))
        items.append((NORMAL, "Tangent", "Move points along mesh tangent only", 2))
        items.append((BVH, "BVH", "Use BVH Tree", 3))
        return items

    preserve_shape : EnumProperty(
            name = "Preserve shape",
            items = get_available_methods,
            update = updateNode)

    skip_bounds : BoolProperty(
            name = "Skip bounds",
            description = "Leave boundary vertices where they were",
            default = True,
            update = updateNode)

    targets = [
            (AVERAGE, "Average", "Average", 0),
            (MINIMUM, "Minimum", "Minimum", 1),
            (MAXIMUM, "Maximum", "Maximum", 2)
        ]

    target : EnumProperty(
            name = "Target",
            items = targets,
            default = AVERAGE,
            update = updateNode)

    use_x: BoolProperty(
        name="X", description="smooth vertices along X axis",
        default=True, update=updateNode)

    use_y: BoolProperty(
        name="Y", description="smooth vertices along Y axis",
        default=True, update=updateNode)

    use_z: BoolProperty(
        name="Z", description="smooth vertices along Z axis",
        default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Edges')
        self.inputs.new('SvStringsSocket', 'Faces')
        self.inputs.new('SvStringsSocket', 'VertMask').enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = "iterations"
        self.inputs.new('SvStringsSocket', 'Factor').prop_name = "factor"

        self.outputs.new('SvVerticesSocket', 'Vertices')
        #self.outputs.new('SvStringsSocket', 'Edges')
        #self.outputs.new('SvStringsSocket', 'Faces')

        self.update_sockets(context)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'algorithm')
        if self.algorithm in {'EDGES', 'FACES'}:
            layout.prop(self, 'target')
        layout.prop(self, 'preserve_shape')
        layout.prop(self, 'skip_bounds')
        row = layout.row(align=True)
        row.prop(self, "use_x", toggle=True)
        row.prop(self, "use_y", toggle=True)
        row.prop(self, "use_z", toggle=True)

    def process(self):
        if not any(output.is_linked for output in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get(deepcopy=False)
        edges_s = self.inputs['Edges'].sv_get(default=[[]], deepcopy=False)
        faces_s = self.inputs['Faces'].sv_get(deepcopy=False)
        masks_s = self.inputs['VertMask'].sv_get(default=[[1]], deepcopy=False)
        iterations_s = self.inputs['Iterations'].sv_get(deepcopy=False)
        factor_s = self.inputs['Factor'].sv_get(deepcopy=False)

        input_level = get_data_nesting_level(vertices_s)
        vertices_s = ensure_nesting_level(vertices_s, 4)
        edges_s = ensure_nesting_level(edges_s, 4)
        faces_s = ensure_nesting_level(faces_s, 4)
        masks_s = ensure_nesting_level(masks_s, 3)
        iterations_s = ensure_nesting_level(iterations_s, 2)
        factor_s = ensure_nesting_level(factor_s, 2)

        nested_output = input_level > 3

        used_axes = set()
        if self.use_x:
            used_axes.add(0)
        if self.use_y:
            used_axes.add(1)
        if self.use_z:
            used_axes.add(2)

        verts_out = []
        for params in zip_long_repeat(vertices_s, edges_s, faces_s, masks_s, iterations_s, factor_s):
            for vertices, edges, faces, mask, iterations, factor in zip_long_repeat(*params):
                if self.algorithm == 'LLOYD':
                    vertices = lloyd_relax(vertices, faces, iterations,
                                    mask = mask,
                                    method = self.preserve_shape,
                                    skip_boundary = self.skip_bounds,
                                    use_axes = used_axes)
                elif self.algorithm == 'EDGES':
                    vertices = edges_relax(vertices, edges, faces, iterations,
                                    k = factor,
                                    mask = mask,
                                    method = self.preserve_shape,
                                    target = self.target,
                                    skip_boundary = self.skip_bounds,
                                    use_axes = used_axes)
                elif self.algorithm == 'FACES':
                    vertices = faces_relax(vertices, edges, faces, iterations,
                                    k = factor,
                                    mask = mask,
                                    method = self.preserve_shape,
                                    target = self.target,
                                    skip_boundary = self.skip_bounds,
                                    use_axes = used_axes)
                else:
                    raise Exception("Unsupported algorithm")

            verts_out.append(vertices)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvRelaxMeshNode)

def unregister():
    bpy.utils.unregister_class(SvRelaxMeshNode)

