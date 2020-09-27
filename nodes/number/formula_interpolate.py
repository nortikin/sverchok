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

import numpy as np

import bpy
from bpy.props import StringProperty, IntProperty, CollectionProperty, FloatProperty, EnumProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode, throttled
from sverchok.data_structure import updateNode, zip_long_repeat, match_long_repeat
from sverchok.utils.logging import info, debug
from sverchok.utils.modules.eval_formula import get_variables, safe_eval
from sverchok.utils.geom import CubicSpline, LinearSpline
from sverchok.utils.curve import SvSplineCurve, SvConcatCurve

class ControlPoint(object):
    def __init__(self, x, y, sharp):
        self.x = x
        self.y = y
        self.sharp = sharp

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.sharp == other.sharp

    def to_tuple(self):
        return (self.x, self.y, 0)

def split_points(points):
    if not points:
        return []
    result = []
    current_segment = []
    n = len(points)
    for i, point in enumerate(points):
        current_segment.append(point)
        if point.sharp and i > 0 and i < n-1:
            result.append(current_segment)
            current_segment = [point]
    result.append(current_segment)
    return result

class SvPointEntry(bpy.types.PropertyGroup):

    def update_point(self, context):
        if hasattr(context, 'node') and hasattr(context.node, 'on_update'):
            context.node.on_update(context)
        else:
            debug("Node is not defined in this context, so will not update the node.")

    x : StringProperty(name = "X", update=update_point)
    y : StringProperty(name = "Y", update=update_point)
    sharp : BoolProperty(name = "Sharp", update=update_point)

class SvPointsList(bpy.types.PropertyGroup):
    points : CollectionProperty(type=SvPointEntry)
    index : IntProperty()

class UI_UL_SvPointUiList(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index, flt_flag):
        if hasattr(data, 'mode'):
            cubic = data.mode == 'SPL'
            n = len(data.control_points)

        row = layout.row(align=True)
        row.prop(item, 'x', text='')
        row.prop(item, 'y', text='')

        if cubic and index > 0 and index < n-1:
            if item.sharp:
                sharp_icon = 'SHARPCURVE'
            else:
                sharp_icon = 'SMOOTHCURVE'
            sharp = row.operator(SvPointSharpToggle.bl_idname, text='', icon=sharp_icon)
            sharp.nodename = data.name
            sharp.treename = data.id_data.name
            sharp.item_index = index

        up = row.operator(SvMovePoint.bl_idname, text='', icon='TRIA_UP')
        up.nodename = data.name
        up.treename = data.id_data.name
        up.item_index = index
        up.shift = -1

        down = row.operator(SvMovePoint.bl_idname, text='', icon='TRIA_DOWN')
        down.nodename = data.name
        down.treename = data.id_data.name
        down.item_index = index
        down.shift = 1

        remove = row.operator(SvRemovePoint.bl_idname, text='', icon='REMOVE')
        remove.nodename = data.name
        remove.treename = data.id_data.name
        remove.item_index = index
    
    def draw_filter(self, context, layout):
        pass

class SvAddPoint(bpy.types.Operator):
    bl_label = "Add control point"
    bl_idname = "sverchok.fi_control_point_add"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        entry = node.control_points.add()
        entry.x = "0"
        entry.y = "0"
        updateNode(node, context)
        return {'FINISHED'}

class SvRemovePoint(bpy.types.Operator):
    bl_label = "Remove control point"
    bl_idname = "sverchok.fi_control_point_remove"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = self.item_index
        node.control_points.remove(idx)
        updateNode(node, context)
        return {'FINISHED'}

class SvMovePoint(bpy.types.Operator):
    "Move control point in the list"

    bl_label = "Move control point"
    bl_idname = "sverchok.fi_control_point_move"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')
    shift : IntProperty(name='shift')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        selected_index = self.item_index
        next_index = selected_index + self.shift
        if (0 <= selected_index < len(node.control_points)) and (0 <= next_index < len(node.control_points)):
            selected_point = node.control_points[selected_index].x, node.control_points[selected_index].y
            next_point = node.control_points[next_index].x, node.control_points[next_index].y
            node.control_points[selected_index].x, node.control_points[selected_index].y = next_point
            node.control_points[next_index].x, node.control_points[next_index].y = selected_point
            updateNode(node, context)
        return {'FINISHED'}

class SvPointSharpToggle(bpy.types.Operator):
    "Make control point sharp / smooth"

    bl_label = "Control point sharp toggle"
    bl_idname = "sverchok.fi_control_point_sharp"
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    nodename : StringProperty(name='nodename')
    treename : StringProperty(name='treename')
    item_index : IntProperty(name='item_index')

    def execute(self, context):
        node = bpy.data.node_groups[self.treename].nodes[self.nodename]
        idx = self.item_index
        node.control_points[idx].sharp = not node.control_points[idx].sharp
        updateNode(node, context)
        return {'FINISHED'}

class SvFormulaInterpolateNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: formula interpolate
    Tooltip: Interpolate between control points specified by formulas
    """

    bl_idname = 'SvFormulaInterpolateNode'
    bl_label = "Formula Interpolate"
    bl_icon = 'MATERIAL'

    control_points : CollectionProperty(type=SvPointEntry)
    selected : IntProperty()

    x_in : FloatProperty(
            name = "X",
            default = 0.5,
            update = updateNode)

    modes = [('SPL', 'Cubic', "Cubic Spline", 0),
             ('LIN', 'Linear', "Linear Interpolation", 1)]
    mode: EnumProperty(name='Interpolation', default="SPL", items=modes, update=updateNode)

    is_cyclic: BoolProperty(name="Cyclic", default=False, update=updateNode)

    def sv_init(self, context):
        self.width = 200
        self.inputs.new('SvStringsSocket', "x").prop_name = 'x_in'
        self.outputs.new('SvStringsSocket', "Result")
        self.outputs.new('SvCurveSocket', "Curve")
        self.outputs.new('SvVerticesSocket', "ControlPoints")

        def add_point(x,y):
            p = self.control_points.add()
            p.x = x
            p.y = y

        add_point("0", "0")
        add_point("0.25", "0.1")
        add_point("0.75", "0.9")
        add_point("1", "1")

    def draw_buttons(self, context, layout):
        layout.template_list("UI_UL_SvPointUiList", "control_points", self, "control_points", self, "selected")
        row = layout.row(align=True)

        add = row.operator(SvAddPoint.bl_idname, text='', icon='ADD')
        add.nodename = self.name
        add.treename = self.id_data.name

        layout.prop(self, 'mode', expand=True)
        layout.prop(self, 'is_cyclic', toggle=True)

    def formulas(self):
        formulas = []
        for point in self.control_points:
            formulas.append(point.x)
            formulas.append(point.y)
        return formulas

    def get_variables(self):
        variables = set()

        for formula in self.formulas():
            vs = get_variables(formula)
            if 'x' in vs:
                raise Exception("The variable `x' must not be used in formulas!")
            variables.update(vs)

        return list(sorted(list(variables)))

    def adjust_sockets(self, variables=None):
        if variables is None:
            variables = self.get_variables()
        #self.debug("adjust_sockets:" + str(variables))
        #self.debug("inputs:" + str(self.inputs.keys()))
        for key in self.inputs.keys():
            if (key not in variables) and (key in self.inputs) and (key != 'x'):
                self.debug("Input {} not in variables {}, remove it".format(key, str(variables)))
                self.inputs.remove(self.inputs[key])
        for v in variables:
            if v not in self.inputs:
                self.debug("Variable {} not in inputs {}, add it".format(v, str(self.inputs.keys())))
                self.inputs.new('SvStringsSocket', v)

    @throttled
    def on_update(self, context):
        self.adjust_sockets()

    def sv_update(self):
        if not any(len(formula) for formula in self.formulas()):
            return
        self.adjust_sockets()

    def get_input(self):
        variables = self.get_variables()
        inputs = {}

        for var in variables:
            if var in self.inputs and self.inputs[var].is_linked:
                inputs[var] = self.inputs[var].sv_get()

        return inputs

    def make_points(self, variables):
        control_points = []
        for item in self.control_points:
            x = safe_eval(item.x, variables)
            y = safe_eval(item.y, variables)
            sharp = item.sharp
            point = ControlPoint(x, y, sharp)
            control_points.append(point)

        control_points.sort(key = lambda p: p.x)
        return split_points(control_points)

    def make_curve(self, control_points):
        curves = []
        for series in control_points:
            xs = [p.x for p in series]
            min_x = xs[0]
            max_x = xs[-1]
            series = np.array([p.to_tuple() for p in series])
            xs = np.array(xs)

            if self.mode == 'SPL':
                spline = CubicSpline(series, tknots=xs, is_cyclic=False)
            else:
                spline = LinearSpline(series, tknots=xs, is_cyclic=False)
            curve = SvSplineCurve(spline)
            curve.u_bounds = (series[0][0], series[-1][0])
            curves.append(curve)

        if len(curves) == 1:
            return curves[0]
        else:
            return SvConcatCurve(curves)

    def eval_spline(self, curve, xs):
        xs = np.array(xs)
        if self.is_cyclic:
            xs = min_x + (xs - min_x) % (max_x - min_x)
        return curve.evaluate_array(xs)[:,1].tolist()
        
    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        x_s = self.inputs['x'].sv_get()

        var_names = self.get_variables()
        inputs = self.get_input()
        input_values = [inputs.get(name, [[0]]) for name in var_names]
        if var_names:
            parameters = match_long_repeat([x_s] + input_values)
        else:
            parameters = [x_s]

        y_out = []
        curve_out = []
        ct_points_out = []
        for xs_in, *objects in zip(*parameters):
            if var_names:
                var_values_s = zip_long_repeat(*objects)
            else:
                var_values_s =[[]]
            for var_values in var_values_s:
                variables = dict(zip(var_names, var_values))
                control_points = self.make_points(variables)
                curve = self.make_curve(control_points)
                ys = self.eval_spline(curve, xs_in)
                y_out.append(ys)
                curve_out.append(curve)
                ct_points_out.append(control_points)

        self.outputs['Result'].sv_set(y_out)
        self.outputs['Curve'].sv_set(curve_out)
        self.outputs['ControlPoints'].sv_set(ct_points_out)

    def load_from_json(self, node_data: dict, import_version: float):
        if import_version <= 0.08:
            self.control_points.clear()
            for x, y in node_data.get('control_points', []):
                entry = self.control_points.add()
                entry.x = x
                entry.y = y
            self.adjust_sockets(variables=node_data.get('variables', []))


classes = [
            SvPointEntry,
            SvPointsList,
            UI_UL_SvPointUiList,
            SvAddPoint,
            SvRemovePoint,
            SvMovePoint,
            SvPointSharpToggle,
            SvFormulaInterpolateNode
        ]

def register():
    for name in classes:
        bpy.utils.register_class(name)

def unregister():
    for name in reversed(classes):
        bpy.utils.unregister_class(name)

