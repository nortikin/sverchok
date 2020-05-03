
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty

import sverchok
from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, ensure_nesting_level, get_data_nesting_level, repeat_last_for_length
from sverchok.utils.logging import info, exception
from sverchok.utils.surface import SvSurface

class SvSurfaceCurvatureLinesNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Surface Curvature Lines
    Tooltip: Generate surface principal curvature lines
    """
    bl_idname = 'SvSurfaceCurvatureLinesNode'
    bl_label = 'Surface Curvature Lines'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_EVAL_SURFACE'

    directions = [
        ('MIN', "Minimum", "Minimum principal curvature direction", 0),
        ('MAX', "Maximum", "Maximum principal curvature direction", 1)
    ]

    direction : EnumProperty(
            name = "Direction",
            items = directions,
            default = 'MIN',
            update = updateNode)

    step : FloatProperty(
            name = "Step",
            min = 0, default = 0.1,
            update = updateNode)

    iterations : IntProperty(
            name = "Iterations",
            min = 1, default = 10,
            update = updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, 'direction', expand=True)

    def sv_init(self, context):
        self.inputs.new('SvSurfaceSocket', "Surface")
        p = self.inputs.new('SvVerticesSocket', "UVPoints")
        p.use_prop = True
        p.prop = (0.5, 0.5, 0.0)
        self.inputs.new('SvStringsSocket', 'Step').prop_name = 'step'
        self.inputs.new('SvStringsSocket', 'Iterations').prop_name = 'iterations'
        self.outputs.new('SvVerticesSocket', "Vertices")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        surfaces_s = self.inputs['Surface'].sv_get()
        surfaces_s = ensure_nesting_level(surfaces_s, 2, data_types=(SvSurface,))
        src_point_s = self.inputs['UVPoints'].sv_get()
        src_point_s = ensure_nesting_level(src_point_s, 4)
        step_s = self.inputs['Step'].sv_get()
        iterations_s = self.inputs['Iterations'].sv_get()

        verts_out = []
        inputs = zip_long_repeat(surfaces_s, src_point_s, step_s, iterations_s)
        for surfaces, src_point_i, step_i, iterations_i in inputs:
            for surface, src_points, step, iterations in zip_long_repeat(surfaces, src_point_i, step_i, iterations_i):
                for src_point in src_points:
                    new_verts = []
                    u,v,_ = src_point
                    for i in range(iterations):
                        vertex = surface.evaluate(u, v).tolist()
                        new_verts.append(vertex)

                        calculator = surface.curvature_calculator(np.array([u]), np.array([v]), order=True)
                        data = calculator.calc(need_uv_directions = True, need_matrix=False)
                        if self.direction == 'MAX':
                            direction = data.principal_direction_2_uv[0]
                        else:
                            direction = data.principal_direction_1_uv[0]
                        direction = direction / np.linalg.norm(direction)
                        direction = direction * step
                        #print(direction)
                        u += direction[0] 
                        v += direction[1]
                        #print(u,v)
                    verts_out.append(new_verts)

        self.outputs['Vertices'].sv_set(verts_out)

def register():
    bpy.utils.register_class(SvSurfaceCurvatureLinesNode)

def unregister():
    bpy.utils.unregister_class(SvSurfaceCurvatureLinesNode)

