import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import kdtree
from mathutils import bvhtree

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.logging import info, exception

from sverchok.utils.field.scalar import SvVoronoiScalarField
from sverchok.utils.field.vector import SvVoronoiVectorField

class SvVoronoiFieldNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Voronoi Field
    Tooltip: Generate Voronoi field
    """
    bl_idname = 'SvExVoronoiFieldNode'
    bl_label = 'Voronoi Field'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_VORONOI'

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")
        self.outputs.new('SvScalarFieldSocket', "SField")
        self.outputs.new('SvVectorFieldSocket', "VField")

    def process(self):

        if not any(socket.is_linked for socket in self.outputs):
            return

        vertices_s = self.inputs['Vertices'].sv_get()

        sfields_out = []
        vfields_out = []
        for vertices in vertices_s:
            sfield = SvVoronoiScalarField(vertices)
            vfield = SvVoronoiVectorField(vertices)
            sfields_out.append(sfield)
            vfields_out.append(vfield)

        self.outputs['SField'].sv_set(sfields_out)
        self.outputs['VField'].sv_set(vfields_out)

def register():
    bpy.utils.register_class(SvVoronoiFieldNode)

def unregister():
    bpy.utils.unregister_class(SvVoronoiFieldNode)

