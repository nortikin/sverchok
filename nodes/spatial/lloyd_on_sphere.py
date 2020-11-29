# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.voronoi3d import lloyd_on_sphere
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvLloydOnSphereNode', "Lloyd on Sphere", 'scipy')

class SvLloydOnSphereNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lloyd Sphere
    Tooltip: Redistribute 3D points on a sphere uniformly by use of Lloyd's algorithm
    """
    bl_idname = 'SvLloydOnSphereNode'
    bl_label = 'Lloyd on Sphere'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    radius: FloatProperty(name="Radius", default=1.0, min=0.0, update=updateNode)

    iterations : IntProperty(
        name = "Iterations",
        description = "Number of Lloyd algorithm iterations",
        min = 0,
        default = 3,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Sites").enable_input_link_menu = False
        d = self.inputs.new('SvVerticesSocket', "Center")
        d.use_prop = True
        d.default_property = (0.0, 0.0, 0.0)
        self.inputs.new('SvStringsSocket', "Radius").prop_name = "radius"
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.inputs.new('SvScalarFieldSocket', 'Weights').enable_input_link_menu = False

        self.outputs.new('SvVerticesSocket', "Sites")

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        center_in = self.inputs['Center'].sv_get()
        radius_in = self.inputs['Radius'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        iterations_in = self.inputs['Iterations'].sv_get()
        weights_in = self.inputs['Weights'].sv_get(default=[[None]])

        center_in = ensure_nesting_level(center_in, 3)
        radius_in = ensure_nesting_level(radius_in, 2)
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        iterations_in = ensure_nesting_level(iterations_in, 2)
        if self.inputs['Weights'].is_linked:
            weights_in = ensure_nesting_level(weights_in, 2, data_types=(SvScalarField,))

        nested_output = input_level > 3

        verts_out = []
        for params in zip_long_repeat(center_in, radius_in, sites_in, iterations_in, weights_in):
            new_verts = []
            for center, radius, sites, iterations, weights in zip_long_repeat(*params):
                sites = lloyd_on_sphere(center, radius, sites, iterations, weights)
                new_verts.append(sites)
            if nested_output:
                verts_out.append(new_verts)
            else:
                verts_out.extend(new_verts)

        self.outputs['Sites'].sv_set(verts_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvLloydOnSphereNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvLloydOnSphereNode)

