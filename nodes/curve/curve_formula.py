
import numpy as np
import math

import bpy
from bpy.props import FloatProperty, EnumProperty, BoolProperty, StringProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, zip_long_repeat,
                                     match_long_repeat, ensure_nesting_level, get_data_nesting_level)
from sverchok.utils.modules.eval_formula import get_variables, sv_compile, safe_eval_compiled
from sverchok.utils.script_importhelper import safe_names_np
from sverchok.utils.math import (
        from_cylindrical, from_spherical,
        from_cylindrical_np, from_spherical_np,
        coordinate_modes
    )
from sverchok.utils.curve import SvLambdaCurve

class SvCurveFormulaNodeMK2(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Curve Formula
    Tooltip: Generate curve by formula
    """
    bl_idname = 'SvExCurveFormulaNodeMK2'
    bl_label = 'Curve Formula'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_CURVE_FORMULA'

    def on_update(self, context):
        self.adjust_sockets()
        updateNode(self, context)

    formula1: StringProperty(
            name = "Formula",
            default = "cos(t)",
            update = on_update)

    formula2: StringProperty(
            name = "Formula",
            default = "sin(t)",
            update = on_update)

    formula3: StringProperty(
            name = "Formula",
            default = "t/(2*pi)",
            update = on_update)

    output_mode : EnumProperty(
        name = "Coordinates",
        items = coordinate_modes,
        default = 'XYZ',
        update = updateNode)

    t_min : FloatProperty(
        name = "T Min",
        description = "Minimum value of the curve’s T parameter",
        default = 0,
        update = updateNode)

    t_max : FloatProperty(
        name = "T Max",
        description = "Maximum value of the curve’s T parameter",
        default = 2*math.pi,
        update = updateNode)

    use_numpy_function : BoolProperty(
        name = "Vectorize",
        description = "Vectorize formula computations; disable this if you have troubles with some functions",
        default = True,
        update = updateNode)

    def sv_init(self, context):
        self.inputs.new('SvStringsSocket', 'TMin').prop_name = 't_min'
        self.inputs.new('SvStringsSocket', 'TMax').prop_name = 't_max'
        self.outputs.new('SvCurveSocket', 'Curve')

    def draw_buttons_ext(self, context, layout):
        self.draw_buttons(context, layout)
        layout.prop(self, 'use_numpy_function')

    def draw_buttons(self, context, layout):
        layout.prop(self, "formula1", text="")
        layout.prop(self, "formula2", text="")
        layout.prop(self, "formula3", text="")
        layout.label(text="Output:")
        layout.prop(self, "output_mode", expand=True)

    def make_function(self, variables):
        compiled1 = sv_compile(self.formula1)
        compiled2 = sv_compile(self.formula2)
        compiled3 = sv_compile(self.formula3)

        if self.output_mode == 'XYZ':
            def out_coordinates(x, y, z):
                return x, y, z
        elif self.output_mode == 'CYL':
            def out_coordinates(rho, phi, z):
                return from_cylindrical(rho, phi, z, mode='radians')
        else: # SPH
            def out_coordinates(rho, phi, theta):
                return from_spherical(rho, phi, theta, mode='radians')

        def function(t):
            variables.update(dict(t=t))
            v1 = safe_eval_compiled(compiled1, variables)
            v2 = safe_eval_compiled(compiled2, variables)
            v3 = safe_eval_compiled(compiled3, variables)
            return np.array(out_coordinates(v1, v2, v3))

        return function

    def make_function_vector(self, variables):
        compiled1 = sv_compile(self.formula1)
        compiled2 = sv_compile(self.formula2)
        compiled3 = sv_compile(self.formula3)

        if self.output_mode == 'XYZ':
            def out_coordinates(x, y, z):
                return x, y, z
        elif self.output_mode == 'CYL':
            def out_coordinates(rho, phi, z):
                return from_cylindrical_np(rho, phi, z, mode='radians')
        else: # SPH
            def out_coordinates(rho, phi, theta):
                return from_spherical_np(rho, phi, theta, mode='radians')

        def function(t):
            variables.update(dict(t=t))
            v1 = safe_eval_compiled(compiled1, variables, allowed_names = safe_names_np)
            v2 = safe_eval_compiled(compiled2, variables, allowed_names = safe_names_np)
            v3 = safe_eval_compiled(compiled3, variables, allowed_names = safe_names_np)

            if not isinstance(v1, np.ndarray):
                v1 = np.full_like(t, v1)
            if not isinstance(v2, np.ndarray):
                v2 = np.full_like(t, v2)
            if not isinstance(v3, np.ndarray):
                v3 = np.full_like(t, v3)

            r = np.array(out_coordinates(v1, v2, v3)).T
            return r

        return function

    def get_coordinate_variables(self):
        return {'t'}

    def get_variables(self):
        variables = set()
        for formula in [self.formula1, self.formula2, self.formula3]:
            new_vars = get_variables(formula)
            variables.update(new_vars)
        variables.difference_update(self.get_coordinate_variables())
        return list(sorted(list(variables)))

    def adjust_sockets(self):
        variables = self.get_variables()
        for key in self.inputs.keys():
            if key not in variables and key not in {'TMin', 'TMax'}:
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

    def sv_update(self):
        if not self.formula1 and not self.formula2 and not self.formula3:
            return
        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()
        return inputs

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        t_min_socket = self.inputs['TMin'].sv_get()
        t_min_level = get_data_nesting_level(t_min_socket)
        if t_min_level==2:
            _t_min_s = ensure_nesting_level(t_min_socket, 2)
            t_min_s3 = [[elem] for elem in _t_min_s]
        elif t_min_level==3:
            t_min_s3 = t_min_socket
            pass
        else:
            raise ValueError("T Min socket has to be 2 or 3 level")
            pass

        t_max_socket = self.inputs['TMax'].sv_get()
        t_max_level = get_data_nesting_level(t_max_socket)
        if t_max_level==2:
            _t_max_s = ensure_nesting_level(t_max_socket, 2)
            t_max_s3 = [[elem] for elem in _t_max_s]
        elif t_max_level==3:
            t_max_s3 = t_max_socket
            pass
        else:
            raise ValueError("T Max socket has to be 2 or 3 level")
            pass

        var_names = self.get_variables()
        inputs = self.get_input()
        _input_values = [inputs.get(name, [[0]]) for name in var_names]
        input_values = []
        for ival_socket in _input_values:
            ival_level = get_data_nesting_level(ival_socket)
            if ival_level==2:
                _ival_socket = ensure_nesting_level(ival_socket, 2)
                ival_s3 = [[elem] for elem in _ival_socket]
            elif ival_level==3:
                ival_s3 = ival_socket
                pass
            else:
                raise ValueError(f"T Min socket has to be 2 or 3 level. {ival_level}")
            pass
            input_values.append(ival_s3)

        curves_out = []
        if var_names:
            lvl1 = match_long_repeat([t_min_s3, t_max_s3] + input_values)
        else:
            lvl1 = [t_min_s, t_max_s]

        for t_min_s, t_max_s, *vars in zip(*lvl1):
            splines = []
            if var_names:
                parameters = [t_min_s, t_max_s, *vars]
            else:
                parameters = [t_min_s, t_max_s]
            
            for t_mins, t_maxs, *var_objects in zip_long_repeat(*parameters):
                
                if var_names:
                    var_values_s = zip_long_repeat(t_mins, t_maxs, *var_objects)
                else:
                    var_values_s = zip_long_repeat(t_mins, t_maxs)

                for t_min, t_max, *var_values in var_values_s:
                    variables = dict(zip(var_names, var_values))
                    function = self.make_function(variables)
                    if self.use_numpy_function:
                        function_vector = self.make_function_vector(variables)
                    else:
                        function_vector = None
                    new_curve = SvLambdaCurve(function, function_vector)
                    new_curve.u_bounds = (t_min, t_max)
                    splines.append(new_curve)
                    pass
                pass
            
            curves_out.append(splines)
        
        self.outputs['Curve'].sv_set(curves_out)

classes = [SvCurveFormulaNodeMK2]
register, unregister = bpy.utils.register_classes_factory(classes)