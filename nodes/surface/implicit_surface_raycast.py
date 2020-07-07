
import numpy as np

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, IntProperty, StringProperty
from mathutils import Vector, Matrix

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat, ensure_nesting_level
from sverchok.utils.logging import info, exception
from sverchok.utils.field.scalar import SvScalarField
from sverchok.utils.dummy_nodes import add_dummy
from sverchok.dependencies import scipy

if scipy is None:
    add_dummy('SvExImplSurfaceRaycastNode', "Implicit Surface Raycast", 'scipy')
else:
    from scipy.optimize import root_scalar

    def goal(field, init, direction, iso_value):
        def function(t):
            p = init + t * direction
            v = field.evaluate(p[0], p[1], p[2])
            return v - iso_value
        return function

    def find_distance(field, init, direction, max_distance, iso_value):
        init_value = field.evaluate(init[0], init[1], init[2])
        sign = (init_value - iso_value)
        distance = max_distance
        max_sections = 10
        i = 0
        while True:
            i += 1
            if i > max_sections:
                raise Exception(f"Can not find range where the field jumps over iso_value: init value at {init} = {init_value}, last value at {distance} = {value}")
            p = init + direction * distance
            value = field.evaluate(p[0], p[1], p[2])
            #print(value)
            if (value - iso_value) * sign < 0:
                break
            distance /= 2.0

        return distance

    def solve(field, init, direction, max_distance, iso_value):
        distance = find_distance(field, init, direction, max_distance, iso_value)
        sol = root_scalar(goal(field, init, direction, iso_value), method = 'ridder',
                x0 = 0,
                bracket = (0, distance)
            )
        t = sol.root
        p = init + t*direction
        return t, p

    class SvExImplSurfaceRaycastNode(bpy.types.Node, SverchCustomTreeNode):
        """
        Triggers: Implicit Surface Raycast
        Tooltip: Raycast onto implicit surface (defined by scalar field)
        """
        bl_idname = 'SvExImplSurfaceRaycastNode'
        bl_label = 'Implicit Surface Raycast'
        bl_icon = 'OUTLINER_OB_EMPTY'

        max_distance : FloatProperty(
                name = "Max Distance",
                default = 10.0,
                min = 0.0,
                update = updateNode)

        iso_value : FloatProperty(
                name = "Iso Value",
                default = 0.0,
                update = updateNode)

        def sv_init(self, context):
            self.inputs.new('SvScalarFieldSocket', "Field")
            p = self.inputs.new('SvVerticesSocket', "Vertices")
            p.use_prop = True
            p.prop = (0.0, 0.0, 0.0)
            p = self.inputs.new('SvVerticesSocket', "Direction")
            p.use_prop = True
            p.prop = (0.0, 0.0, 1.0)
            self.inputs.new('SvStringsSocket', 'IsoValue').prop_name = 'iso_value'
            self.inputs.new('SvStringsSocket', 'MaxDistance').prop_name = 'max_distance'
            self.outputs.new('SvVerticesSocket', 'Vertices')
            self.outputs.new('SvStringsSocket', 'Distance')

        def process(self):
            if not any(socket.is_linked for socket in self.outputs):
                return

            field_s = self.inputs['Field'].sv_get()
            verts_s = self.inputs['Vertices'].sv_get()
            direction_s = self.inputs['Direction'].sv_get()
            iso_value_s = self.inputs['IsoValue'].sv_get()
            max_distance_s = self.inputs['MaxDistance'].sv_get()

            field_s = ensure_nesting_level(field_s, 2, data_types=(SvScalarField,))
            verts_s = ensure_nesting_level(verts_s, 3)
            direction_s = ensure_nesting_level(direction_s, 3)
            iso_value_s = ensure_nesting_level(iso_value_s, 2)
            max_distance_s = ensure_nesting_level(max_distance_s, 2)

            verts_out = []
            distance_out = []

            for fields, verts_i, directions, iso_value_i, max_distance_i in zip_long_repeat(field_s, verts_s, direction_s, iso_value_s, max_distance_s):
                new_verts = []
                new_t = []
                for field, vert, direction, iso_value, max_distance in zip_long_repeat(fields, verts_i, directions, iso_value_i, max_distance_i):
                    direction = np.array(direction)
                    norm = np.linalg.norm(direction)
                    if norm == 0:
                        raise ValueError("Direction vector length is zero!")
                    direction = direction / norm
                    t, p = solve(field, np.array(vert), direction, max_distance, iso_value)
                    #t = t * norm
                    p = tuple(p)
                    new_verts.append(p)
                    new_t.append(t)
                verts_out.append(new_verts)
                distance_out.append(new_t)

            self.outputs['Vertices'].sv_set(verts_out)
            self.outputs['Distance'].sv_set(distance_out)

def register():
    if scipy is not None:
        bpy.utils.register_class(SvExImplSurfaceRaycastNode)

def unregister():
    if scipy is not None:
        bpy.utils.unregister_class(SvExImplSurfaceRaycastNode)

