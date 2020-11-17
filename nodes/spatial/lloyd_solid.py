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
from sverchok.utils.voronoi3d import lloyd_in_solid, lloyd_on_solid_surface
from sverchok.dependencies import scipy, FreeCAD

if scipy is None or FreeCAD is None:
    add_dummy('SvLloydSolidNode', "Lloyd in Solid", 'scipy and FreeCAD')

if FreeCAD is not None:
    import Part

class SvLloydSolidNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Lloyd Solid
    Tooltip: Redistribute 3D points in the volume of a Solid body uniformly by use of Lloyd's algorithm
    """
    bl_idname = 'SvLloydSolidNode'
    bl_label = 'Lloyd in Solid'
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

    @throttle_and_update_node
    def update_sockets(self, context):
        self.inputs['Thickness'].hide_safe = self.mode != 'SURFACE'

    modes = [
            ('VOLUME', "Volume", "Distribute points inside the volume of a Solid body", 0),
            ('SURFACE', "Surface", "Distribute points on the surface of a Solid body", 1)
        ]

    mode : EnumProperty(
        name = "Mode",
        description = "Where to distribute points",
        items = modes,
        default = 'VOLUME',
        update = update_sockets)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", text='')

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvVerticesSocket', "Sites")
        self.inputs.new('SvStringsSocket', 'Thickness').prop_name = 'thickness'
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.outputs.new('SvVerticesSocket', "Sites")
        self.update_sockets(context)

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        solid_in = self.inputs['Solid'].sv_get()
        sites_in = self.inputs['Sites'].sv_get()
        iterations_in = self.inputs['Iterations'].sv_get()
        thickness_in = self.inputs['Thickness'].sv_get()

        solid_in = ensure_nesting_level(solid_in, 2, data_types=(Part.Shape,))
        input_level = get_data_nesting_level(sites_in)
        sites_in = ensure_nesting_level(sites_in, 4)
        iterations_in = ensure_nesting_level(iterations_in, 2)
        thickness_in = ensure_nesting_level(thickness_in, 2)

        nested_output = input_level > 1

        verts_out = []
        for params in zip_long_repeat(solid_in, sites_in, iterations_in, thickness_in):
            new_verts = []
            for solid, sites, iterations, thickness in zip_long_repeat(*params):
                if self.mode == 'VOLUME':
                    sites = lloyd_in_solid(solid, sites, iterations)
                else:
                    sites = lloyd_on_solid_surface(solid, sites, thickness, iterations)

                new_verts.append(sites)
            if nested_output:
                verts_out.append(new_verts)
            else:
                verts_out.extend(new_verts)

        self.outputs['Sites'].sv_set(verts_out)

def register():
    if scipy is not None and FreeCAD is not None:
        bpy.utils.register_class(SvLloydSolidNode)

def unregister():
    if scipy is not None and FreeCAD is not None:
        bpy.utils.unregister_class(SvLloydSolidNode)

