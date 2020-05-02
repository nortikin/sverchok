
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

class SvSurfaceGaussCurvatureNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Gauss Curvature
    Tooltip: Calculate Gauss curvature for the surface at the specified point
    """
    bl_idname = 'SvSurfaceGaussCurvatureNode'
    bl_label = 'Surface Gauss Curvature'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EVAL_SURFACE'

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        self.inputs.new('SvVerticesSocket', "UVPoints")
        self.outputs.new('SvStringsSocket', "Curvature")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        src_point_s = self.inputs['UVPoints'].sv_get()
        src_point_s = ensure_nesting_level(src_point_s, 4)

        curvature_out = []
        for surfaces, src_points_i in zip_long_repeat(surfaces_s, src_point_s):
            for surface, src_points in zip_long_repeat(surfaces, src_points_i):
                us = [p[0] for p in src_points]
                vs = [p[1] for p in src_points]
                curvatures = surface.gauss_curvature_array(np.array(us), np.array(vs)).tolist()
                curvature_out.append(curvatures)

        self.outputs['Curvature'].sv_set(curvature_out)

def register():
    bpy.utils.register_class(SvSurfaceGaussCurvatureNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceGaussCurvatureNode)

