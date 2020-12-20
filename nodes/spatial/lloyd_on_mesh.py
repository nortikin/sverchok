# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
from bpy.props import FloatProperty, StringProperty, BoolProperty, EnumProperty, IntProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, ensure_nesting_level, zip_long_repeat, throttle_and_update_node, get_data_nesting_level
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.voronoi3d import lloyd_on_mesh, lloyd_in_mesh
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvLloydOnMeshNode', "Lloyd on Mesh", 'scipy')

class SvLloydOnMeshNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lloyd Mesh
    Tooltip: Redistribute 3D points on the surface of a mesh uniformly by use of Lloyd's algorithm
    """
    bl_idname = 'SvLloydOnMeshNode'
    bl_label = 'Lloyd on Mesh'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    iterations : IntProperty(
        name = "Iterations",
        description = "Number of Lloyd algorithm iterations",
        min = 0,
        default = 3,
        update = updateNode)

    thickness : FloatProperty(
        name = "Thickness",
        default = 1.0,
        min = 0.0,
        update=updateNode)

    modes = [
            ('SURFACE', "Surface", "Surface", 0),
            ('VOLUME', "Volume", "Volume", 1)
        ]

    mode : bpy.props.EnumProperty(
            name = "Mode",
            items = modes,
            default = 'SURFACE',
            update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode")
    
    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Faces")
        self.inputs.new('SvVerticesSocket', "Sites").enable_input_link_menu = False
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvScalarFieldSocket', 'Weights').enable_input_link_menu = False
        self.outputs.new('SvVerticesSocket', "Sites")

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        verts_in = self.inputs['Vertices'].sv_get()
        faces_in = self.inputs['Faces'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        thickness_in = self.inputs['Thickness'].sv_get()
        iterations_in = self.inputs['Iterations'].sv_get()
        weights_in = self.inputs['Weights'].sv_get(default=[[None]])

        verts_in = ensure_nesting_level(verts_in, 4)
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        faces_in = ensure_nesting_level(faces_in, 4)
        thickness_in = ensure_nesting_level(thickness_in, 2)
        iterations_in = ensure_nesting_level(iterations_in, 2)
        if self.inputs['Weights'].is_linked:
            weights_in = ensure_nesting_level(weights_in, 2, data_types=(SvScalarField,))

        nested_output = input_level > 3

        verts_out = []
        for params in zip_long_repeat(verts_in, faces_in, sites_in, thickness_in, iterations_in, weights_in):
            new_verts = []
            for verts, faces, sites, thickness, iterations, weights in zip_long_repeat(*params):
                if self.mode == 'SURFACE':
                    sites = lloyd_on_mesh(verts, faces, sites, thickness, iterations, weight_field = weights)
                else:
                    sites = lloyd_in_mesh(verts, faces, sites, iterations, thickness=thickness, weight_field = weights)
                new_verts.append(sites)
            if nested_output:
                verts_out.append(new_verts)
            else:
                verts_out.extend(new_verts)

        self.outputs['Sites'].sv_set(verts_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvLloydOnMeshNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvLloydOnMeshNode)

