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
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.voronoi3d import Bounds, lloyd3d_bounded
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvLloyd3dNode', "Lloyd 3D", 'scipy')

class SvLloyd3dNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lloyd Mesh
    Tooltip: Redistribute 3D points within bounding box or sphere uniformly by use of Lloyd's algorithm
    """
    bl_idname = 'SvLloyd3dNode'
    bl_label = 'Lloyd 3D'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    iterations : IntProperty(
        name = "Iterations",
        description = "Number of Lloyd algorithm iterations",
        min = 0,
        default = 3,
        update = updateNode)

    clipping : FloatProperty(
        name = "Clipping",
        default = 1.0,
        min = 0.0,
        update = updateNode)

    modes = [
            ('BOX', "Bounding Box", "Distribute points within bounding box", 0),
            ('SPHERE', "Bounding Sphere", "Distribute points within bounding sphere", 1)
        ]

    bounds_mode : EnumProperty(
        name = "Bounding mode",
        description = "Where to distribute points",
        items = modes,
        default = 'BOX',
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Sites").enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', "Clipping").prop_name = 'clipping'
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.inputs.new('SvScalarFieldSocket', 'Weights').enable_input_link_menu = False
        self.outputs.new('SvVerticesSocket', "Sites")

    def draw_buttons(self, context, layout):
        layout.label(text="Bounds mode:")
        layout.prop(self, "bounds_mode", text='')

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        sites_in = self.inputs['Sites'].sv_get()
        clipping_in = self.inputs['Clipping'].sv_get()
        iterations_in = self.inputs['Iterations'].sv_get()
        weights_in = self.inputs['Weights'].sv_get(default=[[None]])

        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        clipping_in = ensure_nesting_level(clipping_in, 2)
        iterations_in = ensure_nesting_level(iterations_in, 2)
        if self.inputs['Weights'].is_linked:
            weights_in = ensure_nesting_level(weights_in, 2, data_types=(SvScalarField,))

        nested_output = input_level > 3

        verts_out = []
        for params in zip_long_repeat(sites_in, iterations_in, clipping_in, weights_in):
            new_verts = []
            for sites, iterations, clipping, weights in zip_long_repeat(*params):
                bounds = Bounds.new(self.bounds_mode, sites, clipping)
                sites = lloyd3d_bounded(bounds, sites, iterations, weight_field = weights)
                new_verts.append(sites)
            if nested_output:
                verts_out.append(new_verts)
            else:
                verts_out.extend(new_verts)

        self.outputs['Sites'].sv_set(verts_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvLloyd3dNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvLloyd3dNode)

