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
import blf
import os

from bpy.props import (BoolProperty,
                       BoolVectorProperty,
                       EnumProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       IntProperty,
                       StringProperty)

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import node_id, updateNode, match_long_repeat
from sverchok.utils.modules.statistics_functions import *
from sverchok.utils.sv_path_utils import get_fonts_path
from sverchok.settings import get_dpi_factor
from sverchok.ui import bgl_callback_nodeview as nvBGL
from mathutils import Vector
from math import ceil
from pprint import pprint

selectors = {  # Selectors of Statistical Functions
    "ALL_STATISTICS":      (0, "ALL", 0),  # select ALL statistical quantities
    "SELECTED_STATISTICS": (1, "SEL", 0)  # select SOME statistical quantities
}

functions = {  # Statistical Functions > name : (index, abbreviation, function)
    "SUM":                 (10, "SUM", get_sum),
    "SUM_OF_SQUARES":      (11, "SOS", get_sum_of_squares),
    "SUM_OF_INVERSIONS":   (12, "SOI", get_sum_of_inversions),
    "PRODUCT":             (13, "PRD", get_product),
    "AVERAGE":             (14, "AVG", get_average),
    "GEOMETRIC_MEAN":      (15, "GEM", get_geometric_mean),
    "HARMONIC_MEAN":       (16, "HAM", get_harmonic_mean),
    "VARIANCE":            (17, "VAR", get_variance),
    "STANDARD_DEVIATION":  (18, "STD", get_standard_deviation),
    "STANDARD_ERROR":      (19, "STE", get_standard_error),
    "ROOT_MEAN_SQUARE":    (20, "RMS", get_root_mean_square),
    "SKEWNESS":            (21, "SKW", get_skewness),
    "KURTOSIS":            (22, "KUR", get_kurtosis),
    "MINIMUM":             (23, "MIN", get_minimum),
    "MAXIMUM":             (24, "MAX", get_maximum),
    "RANGE":               (25, "RNG", get_range),
    "MEDIAN":              (26, "MED", get_median),
    "PERCENTILE":          (27, "PER", get_percentile),
    "HISTOGRAM":           (28, "HIS", get_histogram),
    "COUNT":               (29, "CNT", get_count)
}

mode_items = [
    ("INT", "Int", "", "", 0),
    ("FLOAT", "Float", "", "", 1)]

function_items = [(k, k.replace("_", " ").title(), "", "", s[0]) for k, s in sorted({**selectors, **functions}.items(), key=lambda k: k[1][0])]

# cache these for faster abbreviation->index and index->abbreviation access
# aTi: SUM->0 , SOS->1 ... CNT->19  and  iTa: 0->SUM , 1->SOS ... 19->CNT
aTi = {v[1]: i for i, v in enumerate(sorted(functions.values(), key=lambda v: v[0]))}
iTa = {i: v[1] for i, v in enumerate(sorted(functions.values(), key=lambda v: v[0]))}
abbreviations = [(i, name) for i, name in sorted(iTa.items(), key=lambda i: i)]

loaded_fonts = {}

font_names = {
    "OCR-A": "OCR-A.ttf",
    "LARABIE": "larabiefont rg.ttf",
    "SHARE_TECH_MONO": "ShareTechMono-Regular.ttf",
    "DATA_LATIN": "DataLatin.ttf",
    "DIGITAL_7": "digital-7 (mono).ttf",
    "DROID_SANS_MONO": "DroidSansMono.ttf",
    "ENVY_CODE": "Envy Code R.ttf",
    "FIRA_CODE": "FiraCode-VF.ttf",
    "HACK": "Hack-Regular.ttf",
    "MONOF55": "monof55.ttf",
    "MONOID_RETINA": "Monoid-Retina.ttf",
    "SAX_MONO": "SaxMono.ttf",
}

font_items = [(k, k.replace("_", " ").title(), "", "", i) for i, k in enumerate(font_names.keys())]


def load_fonts():
    ''' Load fonts '''
    loaded_fonts["main"] = {}

    fonts_path = get_fonts_path()

    # load fonts and create dictionary of Font Name : Font ID
    for font_name, font_filename in font_names.items():
        font_filepath = os.path.join(fonts_path, font_filename)
        font_id = blf.load(font_filepath)
        if font_id >= 0:
            loaded_fonts["main"][font_name] = font_id
        else:  # font not found or could not load? => use blender default font
            loaded_fonts["main"][font_name] = 0


def get_text_drawing_location(node):
    ''' Get the text drawing location relative to the node location '''
    location = Vector((node.absolute_location))
    location = location + Vector((node.width + 20, -20))  # shift right of the node
    location = location + Vector((10*node.text_offset_x,  # apply user offset
                                  10*node.text_offset_y))

    location = location * get_dpi_factor()  # dpi scale adjustment

    return list(location)


class SvStatisticsCallback(bpy.types.Operator):
    bl_label = "Statistics Callback"
    bl_idname = "sv.statistics_callback"
    bl_description = "Callback wrapper class used for operator callbacks"

    function_name: StringProperty()  # name of the function to call

    def execute(self, context):
        n = context.node
        getattr(n, self.function_name)(context)
        return {"FINISHED"}


class SvListStatisticsNode(bpy.types.Node, SverchCustomTreeNode):
    '''
    Triggers: Sum, Avg, Min, Max
    Tooltip: Statistical quantities: sum, average, standard deviation, min, max, product...
    '''
    bl_idname = 'SvListStatisticsNode'
    bl_label = 'List Statistics'
    bl_icon = 'SEQ_HISTOGRAM'
    sv_icon = 'SV_LIST_STADISTICS'

    def update_function(self, context):
        ''' Update sockets and such when the function selection changes '''
        if self.function == "ALL_STATISTICS":
            self.inputs["Percentage"].hide_safe = False
            self.inputs["Bins"].hide_safe = False
            self.inputs["Size"].hide_safe = not self.normalize
            self.outputs[0].name = "Names"
            self.outputs[1].name = "Values"

        elif self.function == "SELECTED_STATISTICS":
            for name in ["Percentage", "Bins", "Size"]:
                self.inputs[name].hide_safe = True
            if self["selected_quantities"][aTi["PER"]]:  # PERCENTILE
                self.inputs["Percentage"].hide_safe = False
            if self["selected_quantities"][aTi["HIS"]]:  # HISTOGRAM
                self.inputs["Bins"].hide_safe = False
                self.inputs["Size"].hide_safe = not self.normalize
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

        self.label = self.function.replace("_", " ").title()
        updateNode(self, context)

    def update_normalize(self, context):
        self.inputs["Size"].hide_safe = not self.normalize
        updateNode(self, context)

    def update_show_statistics(self, context):
        nvBGL.callback_disable(node_id(self))  # clear draw
        updateNode(self, context)

    show_statistics: BoolProperty(
        name="Show Statistics", default=False, update=update_show_statistics)

    text_color: FloatVectorProperty(
        name="Text Color", description='Text color', subtype='COLOR',
        size=3, min=0.0, max=1.0, default=(0.5, 0.3, 1.0), update=updateNode)

    text_scale: FloatProperty(
        name="Text Scale", description='Scale the text size',
        default=1.0, min=0.1, update=updateNode)

    text_offset_x: FloatProperty(
        name="Offset X", description='Offset text along x (10x pixel units)',
        default=0.0, update=updateNode)

    text_offset_y: FloatProperty(
        name="Offset Y", description='Offset text along y (10x pixel units)',
        default=0.0, update=updateNode)

    selected_font: EnumProperty(
        name="Font", items=font_items, default="HACK", update=updateNode)

    precision: IntProperty(
        name="Precision",
        description="Floating point precision of the displayed statistics values",
        min=0, default=2, update=updateNode)

    mode: EnumProperty(
        name="Mode", items=mode_items, default="FLOAT", update=updateNode)

    function: EnumProperty(
        name="Function", description="Selected statistical function(s)",
        items=function_items, update=update_function)

    percentage: FloatProperty(
        name="Percentage",
        description="Percentage value for the percentile statistics",
        default=0.75, min=0.0, max=1.0, update=updateNode)

    bins: IntProperty(
        name="Bins", description="Number of bins in the histogram",
        default=10, min=1, update=updateNode)

    normalize: BoolProperty(
        name="Normalize", description="Normalize the bins to a normalize size",
        default=False, update=update_normalize)

    normalized_size: FloatProperty(
        name="Size", description="The normalized size of the bins",
        default=10.0, update=updateNode)

    abreviate_names: BoolProperty(
        name="Abbreviate Names", description="Abbreviate the statistics quantity names",
        default=False, update=updateNode)

    def toggle_all(self, context):
        self["selected_quantities"] = [self.toggled] * len(functions)
        self.toggled = not self.toggled

    toggled: BoolProperty(
        name="Toggled", description="Statistics toggled",
        default=False, update=update_function)

    def get_array(self):
        return self["selected_quantities"]

    def set_array(self, values):
        self["selected_quantities"] = values

    selected_quantities: BoolVectorProperty(
        name="Selected Quantities", description="Toggle statistic quantities on/off",
        size=len(functions), get=get_array, set=set_array, update=update_function)

    quantities_expanded: BoolProperty(
        name="Expand Quantities", description="Expand the list of statistical quantities",
        default=True)

    def draw_buttons(self, context, layout):
        layout.prop(self, "mode", expand=True)

        col = layout.column(align=True)
        row = col.row(align=True)
        row.prop(self, "function", text="")
        row.prop(self, 'show_statistics', text='', icon='ALIGN_FLUSH')

        if self.function == "SELECTED_STATISTICS":
            box = col.box()
            split = box.split(factor=0.8, align=True)

            c1 = split.column(align=True)
            toggle_button = c1.operator(SvStatisticsCallback.bl_idname, text="Toggle All")
            toggle_button.function_name = "toggle_all"

            c2 = split.column(align=True)
            if self.quantities_expanded:
                c2.prop(self, "quantities_expanded", icon='TRIA_UP', text='')
                # draw the toggle buttons for the selected quantities
                N = int(ceil(len(abbreviations)/4))  # break list into 4 columns
                col = box.column(align=True)
                split = col.split(factor=1/4, align=True)
                for i, name in abbreviations:
                    if i % N == 0:
                        col = split.column(align=True)
                    col.prop(self, "selected_quantities", toggle=True, index=i, text=name)
            else:
                c2.prop(self, "quantities_expanded", icon='TRIA_DOWN', text="")
        # histogram selected? => show the normalize button
        if self.function in ["HISTOGRAM", "ALL_STATISTICS"] or \
                self.function == "SELECTED_STATISTICS" and self["selected_quantities"][aTi["HIS"]]:
            layout.prop(self, "normalize", toggle=True)

    def draw_buttons_ext(self, context, layout):
        box = layout.box()
        # font/text settings
        box.label(text="Font & Text Settings")
        box.prop(self, "selected_font", text="Font")
        box.prop(self, "text_color")
        box.prop(self, "text_scale")
        box.prop(self, "abreviate_names")
        col = box.column(align=True)
        col.prop(self, "text_offset_x")
        col.prop(self, "text_offset_y")
        layout.prop(self, "precision")

    def selected_font_id(self):
        return loaded_fonts["main"][self.selected_font]

    def sv_init(self, context):
        self.width = 160
        self.inputs.new('SvStringsSocket', "Data")
        self.inputs.new('SvStringsSocket', "Percentage").prop_name = "percentage"
        self.inputs.new('SvStringsSocket', "Bins").prop_name = "bins"
        self.inputs.new('SvStringsSocket', "Size").prop_name = "normalized_size"
        self.outputs.new('SvStringsSocket', "Names")
        self.outputs.new('SvStringsSocket', "Values")
        self.function = "AVERAGE"

        self["selected_quantities"] = [True] * len(functions)

    def get_statistics_function(self):
        return functions[self.function][2]  # (0=index, 1=abbreviation, 2=function)

    def draw_statistics(self, names, values):
        """ Draw the statistics in the node editor

        The statistics data can be either single or vectorized.
        * single:
        [ [sum], [avg], ... [[b1, b2, .. bN]] ]
        * vectorized:
        [ [sum1... sumM], [avg1... avgM], ... [[b11... b1N]... [bM1... bMN]] ]

        Q: how can we tell statistics are simple or vectorized?
        A: if the values[0] is a list with length > 1 then it's vectorized
        """
        nvBGL.callback_disable(node_id(self))  # clear drawing

        if len(values) == 0:
            return

        if self.show_statistics:
            max_width = max(len(name) for name in names)  # used for text alignment

            info = []

            # for now let's treat single and vectorized separately (optimize later)
            is_vectorized = len(values[0]) > 1

            if is_vectorized:
                for n, v in zip(names, values):
                    if n in ["Histogram", "HIS"]:
                        line_format = "{0:>{x}} : [{1}]"
                        histogram_lines = []
                        for a in v:  # for each histogram set
                            if self.mode == "FLOAT":
                                value_format = "{:.{p}f}"
                            else:
                                value_format = "{}"
                            histogram_values = ", ".join([value_format.format(aa, p=self.precision) for aa in a])
                            histogram_lines.append("[{}]".format(histogram_values))
                        line = line_format.format(n, ", ".join(histogram_lines), x=max_width)
                        info.append(line)

                    else:
                        line_format = "{0:>{x}} : [{1}]"
                        if n in ["Count", "CNT"]:
                            value_format = "{}"
                        else:
                            if self.mode == "FLOAT":
                                value_format = "{:.{p}f}"
                            else:
                                value_format = "{}"

                        value_line = ", ".join([value_format.format(vv, p=self.precision) for vv in v])
                        line = line_format.format(n, value_line, x=max_width)

                        info.append(line)
            else:  # single values
                for n, v in zip(names, values):
                    if n in ["Histogram", "HIS"]:
                        # print("drawing histogram")
                        line_format = "{0:>{x}} : [{1}]"
                        if self.normalize:
                            value_format = "{:.{p}f}"
                        else:
                            value_format = "{}"
                        histogram_values = ", ".join([value_format.format(a, p=self.precision) for a in v[0]])
                        line = line_format.format(n, histogram_values, x=max_width)
                        info.append(line)
                    else:
                        if n in ["Count", "CNT"]:
                            line_format = "{0:>{x}} : {1}"
                        else:
                            if self.mode == "FLOAT":
                                line_format = "{0:>{x}} : {1:.{p}f}"
                            else:
                                line_format = "{0:>{x}} : {1}"

                        line = line_format.format(n, v[0], x=max_width, p=self.precision)

                        info.append(line)

            draw_data = {
                'tree_name': self.id_data.name[:],
                'node_name': self.name[:],
                'content': info,
                'location': get_text_drawing_location,
                'color': self.text_color[:],
                'scale': self.text_scale * get_dpi_factor(),
                'font_id': int(self.selected_font_id())
            }

            nvBGL.callback_enable(node_id(self), draw_data)

    def sv_free(self):
        nvBGL.callback_disable(node_id(self))

    def process(self):
        inputs = self.inputs
        outputs = self.outputs

        # no inputs are connected ? => return
        if not any(s.is_linked for s in inputs):
            nvBGL.callback_disable(node_id(self))  # clear drawing
            return

        # no outputs are connected or statistics are not shown? => return
        if not self.show_statistics:
            if not any(s.is_linked for s in outputs):
                nvBGL.callback_disable(node_id(self))  # clear drawing
                return

        input_D = inputs["Data"].sv_get(default=[[]])

        if len(input_D) == 0 or any([len(d) == 0 for d in input_D]):
            outputs[0].sv_set([[]])
            outputs[1].sv_set([[]])
            raise Exception("Input data contains empty lists")

        input_P = inputs["Percentage"].sv_get()[0]
        input_B = inputs["Bins"].sv_get()[0]
        input_S = inputs["Size"].sv_get()[0]

        # sanitize the inputs
        input_P = list(map(lambda x: max(0, min(1, x)), input_P))
        input_B = list(map(lambda x: max(1, x), input_B))

        if self.mode == "INT":
            input_P = list(map(lambda x: int(x), input_P))

        # determine the list of functions to generate statistics for
        if self.function == "ALL_STATISTICS":
            function_names = list(functions.keys())

        elif self.function == "SELECTED_STATISTICS":
            function_names = []
            for i, f in enumerate(functions.keys()):
                if self["selected_quantities"][i]:
                    function_names.append(f)

        else:  # one statistical quantity
            function_names = [self.function]

        params = match_long_repeat([input_D, input_P, input_B, input_S])

        all_names = []
        all_values = []
        for function_name in function_names:
            statistics_function = functions[function_name][2]  # (0=index, 1=abbreviation, 2=function)
            quantity_list = []
            for d, p, b, s in zip(*params):
                if function_name == "PERCENTILE":
                    quantity = statistics_function(d, p)
                elif function_name == "HISTOGRAM":
                    quantity = statistics_function(d, b, self.normalize, s)
                else:
                    quantity = statistics_function(d)

                if function_name != "HISTOGRAM":
                    if self.mode == "INT":
                        quantity = int(quantity)

                quantity_list.append(quantity)

            if self.abreviate_names:
                name = functions[function_name][1]  # (0=index, 1=abbreviation, 2=function)
            else:
                name = function_name.replace("_", " ").title()

            all_names.append(name)
            all_values.append(quantity_list)

        if outputs[0].is_linked:
            outputs[0].sv_set(all_names)
        if outputs[1].is_linked:
            outputs[1].sv_set(all_values)

        self.draw_statistics(all_names, all_values)


def register():
    bpy.utils.register_class(SvStatisticsCallback)
    bpy.utils.register_class(SvListStatisticsNode)
    load_fonts()


def unregister():
    bpy.utils.unregister_class(SvListStatisticsNode)
    bpy.utils.unregister_class(SvStatisticsCallback)


if __name__ == '__main__':
    register()
