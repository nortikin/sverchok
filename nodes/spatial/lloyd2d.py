# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, ensure_nesting_level, zip_long_repeat, get_data_nesting_level
from sverchok.utils.voronoi import lloyd2d
from sverchok.utils.field.scalar import SvScalarField

class SvLloyd2dNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lloyd 2D
    Tooltip: Redistribute 2D points uniformly by use of Lloyd's algorithms
    """
    bl_idname = 'SvLloyd2dNode'
    bl_label = 'Lloyd 2D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    clip: FloatProperty(
        name='clip', description='Clipping Distance',
        default=1.0, min=0, update=updateNode)

    bound_modes = [
            ('BOX', 'Bounding Box', "Bounding Box", 0),
            ('CIRCLE', 'Bounding Circle', "Bounding Circle", 1)
        ]

    bound_mode: EnumProperty(
        name = 'Bounds Mode',
        description = "Bounding mode",
        items = bound_modes,
        default = 'BOX',
        update = updateNode)

    iterations : IntProperty(
        name = "Iterations",
        description = "Number of Lloyd algorithm iterations",
        min = 0,
        default = 3,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.inputs.new('SvScalarFieldSocket', 'Weights').enable_input_link_menu = False
        self.outputs.new('SvVerticesSocket', "Vertices")

    def draw_buttons(self, context, layout):
        layout.label(text="Bounds mode:")
        layout.prop(self, "bound_mode", text='')
    
    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, "clip", text="Clipping")

    def process(self):

        if not self.outputs['Vertices'].is_linked:
            return

        verts_in = self.inputs['Vertices'].sv_get()
        iterations_in = self.inputs['Iterations'].sv_get()
        weights_in = self.inputs['Weights'].sv_get(default=[[None]])

        input_level = get_data_nesting_level(verts_in)
        verts_in = ensure_nesting_level(verts_in, 4)
        iterations_in = ensure_nesting_level(iterations_in, 2)
        if self.inputs['Weights'].is_linked:
            weights_in = ensure_nesting_level(weights_in, 2, data_types=(SvScalarField,))

        nested_output = input_level > 3

        verts_out = []
        for params in zip_long_repeat(verts_in, iterations_in, weights_in):
            new_verts = []
            for verts, iterations, weights in zip_long_repeat(*params):
                iter_verts = lloyd2d(self.bound_mode, verts, iterations,
                                clip = self.clip, weight_field = weights)
                new_verts.append(iter_verts)
            if nested_output:
                verts_out.append(new_verts)
            else:
                verts_out.extend(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvLloyd2dNode)

def unregister():
    bpy.utils.unregister_class(SvLloyd2dNode)

