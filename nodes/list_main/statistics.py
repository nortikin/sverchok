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
from bpy.props import EnumProperty, IntProperty, FloatProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat
from sverchok.utils.modules.statistics_functions import *

functions = {
    "ALL_STATISTICS":     (0, 0),
    "SUM":                (10, get_sum),
    "SUM_OF_SQUARES":     (11, get_sum_of_squares),
    "SUM_OF_INVERSIONS":  (12, get_sum_of_inversions),
    "PRODUCT":            (13, get_product),
    "AVERAGE":            (14, get_average),
    "GEOMETRIC_MEAN":     (15, get_geometric_mean),
    "HARMONIC_MEAN":      (16, get_harmonic_mean),
    "STANDARD_DEVIATION": (17, get_standard_deviation),
    "ROOT_MEAN_SQUARE":   (18, get_root_mean_square),
    "SKEWNESS":           (19, get_skewness),
    "KURTOSIS":           (20, get_kurtosis),
    "MINIMUM":            (21, get_minimum),
    "MAXIMUM":            (22, get_maximum),
    "MEDIAN":             (23, get_median),
    "PERCENTILE":         (24, get_percentile),
    "HISTOGRAM":          (25, get_histogram)
}


modeItems = [
    ("INT", "Int", "", "", 0),
    ("FLOAT", "Float", "", "", 1)]

functionItems = [(k, k.replace("_", " ").title(), "", "", s[0]) for k, s in sorted(functions.items(), key=lambda k: k[1][0])]


class SvListStatisticsNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Sum, Avg, Min, Max
    Tooltip: Statistical quantities: sum, average, standard deviation, min, max, product...
    '''
    bl_idname = 'SvListStatisticsNode'
    bl_label = 'List Statistics'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_LIST_STADISTICS'

    def update_function(self, context):
        if self.function == "ALL STATISTICS":
            self.inputs["Percentage"].hide_safe = False
            self.inputs["Bins"].hide_safe = False
            self.inputs["Size"].hide_safe = not self.normalize
            self.outputs[0].name = "Names"
            self.outputs[1].name = "Values"
        else:
            for name in ["Percentage", "Bins", "Size"]:
                self.inputs[name].hide_safe = True
            if self.function == "PERCENTILE":
                self.inputs["Percentage"].hide_safe = False
            elif self.function == "HISTOGRAM":
                self.inputs["Bins"].hide_safe = False
                self.inputs["Size"].hide_safe = not self.normalize

            self.outputs[0].name = "Name"
            self.outputs[1].name = "Value"

        updateNode(self, context)

    def update_normalize(self, context):
        socket = self.inputs["Size"]
        socket.hide_safe = not self.normalize

        updateNode(self, context)

    mode : EnumProperty(
        name="Mode", items=modeItems, default="FLOAT", update=updateNode)

    function : EnumProperty(
        name="Function", items=functionItems, update=update_function)

    percentage : FloatProperty(
        name="Percentage",
        default=0.75, min=0.0, max=1.0, update=updateNode)

    bins : IntProperty(
        name="Bins",
        default=10, min=1, update=updateNode)

    normalize : BoolProperty(
        name="Normalize", description="Normalize the bins to a normalize size",
        default=False, update=update_normalize)

    normalized_size : FloatProperty(
        name="Size", description="The normalized size of the bins",
        default=10.0, update=updateNode)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)
        layout.prop(self, "function", text="")
        if self.function in ["HISTOGRAM", "ALL STATISTICS"]:
            layout.prop(self, "normalize", toggle=True)

    def sv_init(self, context):
        self.width = 150
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvStringsSocket', "Percentage").prop_name = "percentage"
        self.inputs.new('SvStringsSocket', "Bins").prop_name = "bins"
        self.inputs.new('SvStringsSocket', "Size").prop_name = "normalized_size"
        self.outputs.new('SvStringsSocket', "Names")
        self.outputs.new('SvStringsSocket', "Values")
        self.function = "AVERAGE"

    def get_statistics_function(self):
        return functions[self.function][1]

    def process(self):
        outputs = self.outputs
        # return if no outputs are connected
        if not any(s.is_linked for s in outputs):
            return

        inputs = self.inputs
        input_D = inputs["Data"].sv_get()
        input_P = inputs["Percentage"].sv_get()[0]
        input_B = inputs["Bins"].sv_get()[0]
        input_S = inputs["Size"].sv_get()[0]

        # sanitize the inputs
        input_P = list(map(lambda x: max(0, min(1, x)), input_P))
        input_B = list(map(lambda x: max(1, x), input_B))

        if self.mode == "INT":
            input_P = list(map(lambda x: int(x), input_P))

        if self.function == "ALL_STATISTICS":
            functionNames = [fn[0] for fn in functionItems[1:]]
        else:
            functionNames = [self.function]

        params = match_long_repeat([input_D, input_P, input_B, input_S])

        allNames = []
        allValues = []
        for functionName in functionNames:
            statistics_function = functions[functionName][1]
            quantityList = []
            for d, p, b, s in zip(*params):
                if functionName == "PERCENTILE":
                    quantity = statistics_function(d, p)
                elif functionName == "HISTOGRAM":
                    quantity = statistics_function(d, b, self.normalize, s)
                else:
                    quantity = statistics_function(d)

                if functionName != "HISTOGRAM":
                    if self.mode == "INT":
                        quantity = int(quantity)

                quantityList.append(quantity)

            allNames.append(functionName)
            allValues.append(quantityList)

        outputs[0].sv_set(allNames)
        outputs[1].sv_set(allValues)


def register():
    bpy.utils.register_class(SvListStatisticsNode)


def unregister():
    bpy.utils.unregister_class(SvListStatisticsNode)
