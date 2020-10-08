# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy
from bpy.props import EnumProperty, IntProperty, FloatProperty, FloatVectorProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (zip_long_repeat, enum_item_4, updateNode)
from sverchok.utils.pulga_physics_modular_core import (
    SvBoundingBoxForce,
    SvBoundingSphereForce,
    SvBoundingSphereSurfaceForce,
    SvBoundingPlaneSurfaceForce,
    SvBoundingMeshForce,
    SvBoundingSolidForce)
from sverchok.dependencies import FreeCAD

class SvPulgaBoundingBoxForceNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Spacial Ambit
    Tooltip: Define simulation Limits by Volume or Surface
    """
    bl_idname = 'SvPulgaBoundingBoxForceNode'
    bl_label = 'Pulga Boundaries Force'
    bl_icon = 'MOD_PHYSICS'
    sv_icon = 'SV_PULGA_BOUNDARIES_FORCE'

    def update_sockets_and_node(self, context):
        self.update_sockets()
        updateNode(self, context)

    def update_sockets(self):
        self.inputs['Bounding Box'].hide_safe = self.mode != 'Box'
        self.inputs['Center'].hide_safe = not 'Sphere' in self.mode and not 'Plane' in self.mode
        self.inputs['Radius'].hide_safe = not 'Sphere' in self.mode
        self.inputs['Normal'].hide_safe = not 'Plane' in self.mode
        self.inputs['Vertices'].hide_safe = not 'Mesh' in self.mode
        self.inputs['Polygons'].hide_safe = not 'Mesh' in self.mode
        self.inputs['Solid'].hide_safe = not 'Solid_(' in self.mode
        self.inputs['Solid Face'].hide_safe = self.mode != 'Solid_Face'

    mode_items=['Box', 'Sphere', 'Sphere Surface', 'Plane', 'Mesh (Surface)', 'Mesh (Volume)']
    if FreeCAD is not None:
        mode_items.append('Solid (Surface)')
        mode_items.append('Solid (Volume)')
        mode_items.append('Solid Face')

    mode: EnumProperty(
        name='Mode', description='Boundaries definition mode',
        items=enum_item_4(mode_items),
        default='Box',
        update=update_sockets_and_node)
    center: FloatVectorProperty(
        name='Center',
        description='Bunding Shpere center',
        default=(0,0,0),
        size=3,
        update=updateNode)
    radius: FloatProperty(
        name='Radius',
        description='Bunding Shpere radius',
        default=0.0,
        update=updateNode)
    normal: FloatVectorProperty(
        name='Normal',
        description='Bunding Shpere center',
        default=(0, 0, 0),
        size=3,
        update=updateNode)

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Bounding Box")
        self.inputs.new('SvVerticesSocket', "Center").prop_name = 'center'
        self.inputs.new('SvStringsSocket', "Radius").prop_name = 'radius'
        self.inputs.new('SvVerticesSocket', "Normal").prop_name = 'normal'
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.inputs.new('SvStringsSocket', "Polygons")
        self.inputs.new('SvSolidSocket', "Solid")
        self.inputs.new('SvSurfaceSocket', "Solid Face")
        self.update_sockets()

        self.outputs.new('SvPulgaForceSocket', "Force")

    def draw_buttons(self, context, layout):
        layout.prop(self, 'mode')

    def process(self):

        if not any(s.is_linked for s in self.outputs):
            return
        if self.mode == 'Box':
            b_box = self.inputs["Bounding Box"].sv_get(deepcopy=False)

            forces_out = []
            for force in b_box:
                forces_out.append(SvBoundingBoxForce(force))
        elif self.mode == 'Sphere':

            center = self.inputs["Center"].sv_get(deepcopy=False)
            radius = self.inputs["Radius"].sv_get(deepcopy=False)

            forces_out = []
            for force in zip_long_repeat(center, radius):
                forces_out.append(SvBoundingSphereForce(*force))
        elif self.mode == 'Sphere_Surface':

            center = self.inputs["Center"].sv_get(deepcopy=False)
            radius = self.inputs["Radius"].sv_get(deepcopy=False)

            forces_out = []
            for force in zip_long_repeat(center, radius):
                forces_out.append(SvBoundingSphereSurfaceForce(*force))
        elif self.mode == 'Plane':

            center = self.inputs["Center"].sv_get(deepcopy=False)
            radius = self.inputs["Normal"].sv_get(deepcopy=False)

            forces_out = []
            for force in zip_long_repeat(center, radius):
                forces_out.append(SvBoundingPlaneSurfaceForce(*force))
        elif 'Mesh' in self.mode:

            verts = self.inputs["Vertices"].sv_get(deepcopy=False)
            polygons = self.inputs["Polygons"].sv_get(deepcopy=False)
            volume = self.mode == "Mesh_(Volume)"
            forces_out = []
            for force in zip_long_repeat(verts, polygons):
                forces_out.append(SvBoundingMeshForce(*force, volume))

        elif 'Solid' in self.mode:
            input_name = 'Solid' if self.mode in ['Solid_(Surface)', 'Solid_(Volume)'] else 'Solid Face'
            solid = self.inputs[input_name].sv_get(deepcopy=False)
            volume = self.mode == "Solid_(Volume)"
            forces_out = []
            for force in solid:
                forces_out.append(SvBoundingSolidForce(force, volume=volume))

        self.outputs[0].sv_set([forces_out])



def register():
    bpy.utils.register_class(SvPulgaBoundingBoxForceNode)


def unregister():
    bpy.utils.unregister_class(SvPulgaBoundingBoxForceNode)
