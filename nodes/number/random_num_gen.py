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

from math import isclose

import bpy
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, match_long_repeat, fullList


class SvRndNumGen(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Random thru a range
    Tooltip: Generate a random number (int of float) thru a given range (inclusive) .
    """
    bl_idname = 'SvRndNumGen'
    bl_label = 'Random Num Gen'
    bl_icon = 'OUTLINER_OB_EMPTY'
    sv_icon = 'SV_RANDOM_NUM_GEN'

    low_f: FloatProperty(
        name='Float Low', description='Minimum float value',
        default=0.0, update=updateNode)

    high_f : FloatProperty(
        name='Float High', description='Maximum float value',
        default=1.0, update=updateNode)

    low_i : IntProperty(
        name='Int Low', description='Minimum integer value',
        default=0, update=updateNode)

    high_i : IntProperty(
        name='Int High', description='Maximum integer value',
        default=10, update=updateNode)

    size : IntProperty(
        name='Size', description='number of values to output (count.. or size)',
        default=10, min=1, update=updateNode)

    seed : IntProperty(
        name='Seed', description='seed, grow',
        default=0, min=0, update=updateNode)

    alpha : FloatProperty(
        name='Alpha', description='Distribution parameter',
        default=2.0, min=(1e-06), update=updateNode)

    beta : FloatProperty(
        name='Beta', description='Distribution parameter',
        default=2.0, min=(1e-06), update=updateNode)

    t_in : FloatProperty(
         name="t", description='Distribution parameter',
         default=.5, min=1e-06, max=1.0-1e-06, precision=6, update=updateNode)


    as_list : BoolProperty(
        name='As List', description='on means output list, off means output np.array 1d',
        default=True, update=updateNode)

    def numpy_bridge(self, context):
        self.as_list = not self.output_numpy
    output_numpy : BoolProperty(
        name='Output Numpy', description='Output numpy arrays',
        default=False, update=numpy_bridge)


    func_dict = {
        "UNIFORM":       (0, np.random.ranf,                  [0],          False, "Uniform",               (1e-06, 1e-06)),
        "BETA":          (1, np.random.beta,                  [1, 2, 0],    False, "Beta",                  (1e-06, 1e-06)),
        "BINOMIAL":      (2, np.random.binomial,              [1, 3, 0],    True,  "Binomial",              (1e-06, 1e-06)),
        "CHI_SQUARE":    (3, np.random.chisquare,             [1, 0],       True,  "Chi_square",            (1e-06, 1e-06)),
        "EXPONENTIAL":   (4, np.random.exponential,           [6, 0],       True,  "Exponential",           (1e-06, 1e-06)),
        "F_DIST":        (5, np.random.f,                     [1, 2, 0],    True,  "F Distrib.",            (1e-06, 0.025)),
        "GAMMA":         (6, np.random.gamma,                 [1, 6, 0],    True,  "Gamma",                 (1e-06, 1e-06)),
        "GEOMETRIC":     (7, np.random.geometric,             [3, 0],       True,  "Geometric",             (1e-06, 1e-06)),
        "GUMBEL":        (8, np.random.gumbel,                [6, 6, 0],    True,  "Gumbel",                (1e-06, 1e-06)),
        "LAPLACE":       (9,  np.random.laplace,              [6, 6, 0],    True,  "Laplace",               (1e-06, 1e-06)),
        "LOGISTIC":      (10, np.random.logistic,             [6, 6, 0],    True,  "Logistic",              (1e-06, 1e-06)),
        "LOG_NORMAL":    (11, np.random.lognormal,            [6, 1, 0],    True,  "Log Normal",            (1e-06, 1e-06)),
        "LOG_SERIES":    (12, np.random.logseries,            [3, 0],       True,  "Log Series",            (1e-06, 1e-06)),
        "NEG_BINOMIAL":  (13, np.random.negative_binomial,    [1, 3, 0],    True,  "Negative Binomial",     (1e-06, 1e-06)),
        "NONCEN_CHI_SQ": (14, np.random.noncentral_chisquare, [1, 2, 0],    True,  "Noncentred Chi-Square", (1e-06, 1e-06)),
        "NORMAL":        (15, np.random.normal,               [6, 6, 0],    True,  "Normal",                (1e-06, 1e-06)),
        "PARETO":        (16, np.random.pareto,               [1, 0],       True,  "Pareto",                (0.01,  1e-06)),
        "POISSON":       (17, np.random.poisson,              [6, 0],       True,  "Poisson",               (1e-06, 1e-06)),
        "POWER":         (18, np.random.power,                [1, 0],       True,  "Power",                 (1e-06, 1e-06)),
        "RAYLEIGH":      (19, np.random.rayleigh,             [6, 0],       True,  "RayLeigh",              (1e-06, 1e-06)),
        "STD_CAUCHY":    (20, np.random.standard_cauchy,      [0],          True,  "Standard Cauchy",       (1e-06, 1e-06)),
        "STD_GAMMA":     (22, np.random.standard_gamma,       [6, 0],       True,  "Standard Gamma",        (1e-06, 1e-06)),
        "STD_T":         (24, np.random.standard_t,           [1, 0],       True,  "Standard T",            (0.017, 1e-06)),
        "TRIANGULAR":    (25, np.random.triangular,           [4, 1, 5, 0], False, "Triangular",            (1e-06, 1e-06)),
        "VONMISES":      (26, np.random.vonmises,             [1, 2, 0],    True,  "Vonmises",              (1e-06, 1e-06)),
        "WALD":          (27, np.random.wald,                 [1, 2, 0],    True,  "Wald",                  (1e-06, 1e-06)),
        "WEIBULL":       (28, np.random.weibull,              [1, 0],       True,  "Weibull",               (0.0028, 1e-06)),
        "ZIPF":          (29, np.random.zipf,                 [1, 0],       True,  "Zipf",                  (1+1e-05, 1e-06)),
    }

    distribute_options = [(key, value[4], "", value[0]) for key, value in sorted(func_dict.items())]

    soket_opt = [
        ('Alpha', 'alpha', 1),
        ('Beta', 'beta', 2),
        ('t', 't_in', 3)]

    def adjust_inputs(self, context):
        m = self.type_selected_mode
        si = self.inputs
        ssk = self.soket_opt
        if m == 'Int':
            if si[2].prop_name[-1] == 'f':
                si[2].prop_name = 'low_i'
                si[3].prop_name = 'high_i'
            si['Weights'].hide_safe = not self.weighted
            for i in range(0, 3):
                si[ssk[i][0]].hide_safe = True

        elif m == 'Float':
            dsm = self.distribute_mode
            func = self.func_dict[dsm]
            if si[2].prop_name[-1] == 'i':
                si[2].prop_name = 'low_f'
                si[3].prop_name = 'high_f'
            si['Weights'].hide_safe = True
            for i in range(1, 4):
                si[ssk[i-1][0]].hide_safe = i not in func[2]

        updateNode(self, context)

    type_mode_options = [
        ("Int", "Int", "", 0),
        ("Float", "Float", "", 1)
    ]

    type_selected_mode : EnumProperty(
        items=type_mode_options, description="offers....",
        default="Int", update=adjust_inputs
    )

    weighted : BoolProperty(
        name='Weighted', description='Input probability for each number',
        default=False, update=adjust_inputs)

    unique : BoolProperty(
        name='Unique', description='Output non-repeated numbers',
        default=False, update=updateNode)

    distribute_mode : EnumProperty(
        name="Distribution", description="Distribution method",
        items=distribute_options,
        default="UNIFORM", update=adjust_inputs
    )

    def sv_init(self, context):
        si = self.inputs
        si.new('SvStringsSocket', "Size").prop_name = 'size'
        si.new('SvStringsSocket', "Seed").prop_name = 'seed'
        si.new('SvStringsSocket', "Low").prop_name = 'low_i'
        si.new('SvStringsSocket', "High").prop_name = 'high_i'
        si.new('SvStringsSocket', 'Weights').hide_safe = not self.weighted

        ssk = self.soket_opt
        func = self.func_dict[self.distribute_mode]
        m = self.type_selected_mode
        for i in range(1, 4):
            si.new('SvStringsSocket', ssk[i-1][0]).prop_name = ssk[i-1][1]
            si[ssk[i-1][0]].hide_safe = ((m == "Int") or i not in func[2])

        so = self.outputs
        so.new('SvStringsSocket', "Value")

    def buttons(self, layout):
        row = layout.row()
        row.prop(self, 'type_selected_mode', expand=True)
        if self.type_selected_mode == "Int":
            c1 = layout.row(align=True)
            c1.prop(self, "unique", toggle=True )
            c1.prop(self, "weighted", toggle=True)
        else:
            layout.prop(self, "distribute_mode")

    def draw_buttons(self, context, layout):
        self.buttons(layout)

    def draw_buttons_ext(self, context, layout):
        self.buttons(layout)
        layout.prop(self, "as_list", invert_checkbox=True, text="Output NumPy")

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "type_selected_mode", text="Number Type: "+ self.type_selected_mode)
        if self.type_selected_mode == "Int":
            layout.prop(self, "unique", toggle=True )
            layout.prop(self, "weighted", toggle=True)
        else:
            layout.prop_menu_enum(self, "distribute_mode")
        layout.prop(self, "output_numpy", toggle=True, text="Output NumPy")


    def int_random_range(self, *params):
        if len(params) < 5:
            size, seed, low, high = params
            weights = []
        else:
            size, seed, low, high, weights = params
        size = max(size, 1)
        if self.unique:
           size = min(size,high + 1 - low)
        seed = max(seed, 0)
        np.random.seed(seed)
        low, high = sorted([low, high])
        population = range(low, high + 1)

        if self.weighted and len(weights) > 0:
            fullList(weights, size)
            weights = weights[:size]
            total_weight = sum(weights)
            weights = [w / total_weight for w in weights]
            result = np.random.choice(population, size, replace=(not self.unique), p=weights)
        else:
           result = np.random.choice(population, size, replace=(not self.unique))

        return result

    def float_random_range(self, *params):
        func = self.func_dict[self.distribute_mode]
        alpha = 0.5
        beta = 1
        t_in = 1
        if len(params) < 5:
            size, seed, low, high = params
        elif len(params) == 6:
            if 2 in func[2]:
                size, seed, low, high, alpha, beta = params
            elif 3 in func[2]:
                size, seed, low, high, alpha, t_in = params

        elif len(params) == 5:
            if 1 in func[2]:
                size, seed, low, high, alpha = params
            elif 3 in func[2]:
                size, seed, low, high, t_in = params
        alpha = max(alpha, func[5][0])
        beta = max(beta, func[5][1])
        size = max(size, 1)
        seed = max(seed, 0)
        t_in = min(max(t_in, 1e-06), 1-1e-06)

        args = [size, alpha, beta, t_in, low, high, 1]
        args = [args[i] for i in func[2]]

        np.random.seed(seed)
        result = func[1](*args)

        if func[3]:
            min_v = (np.ndarray.min(result))
            max_v = (np.ndarray.max(result))
        else:
            min_v = 0.0
            max_v = 1.0

        epsilon_relative = 1e-06
        if isclose(low, min_v, rel_tol=epsilon_relative) and isclose(high, max_v, rel_tol=epsilon_relative):
            pass
        else:
            my_func = lambda inval: np.interp(inval, [min_v, max_v], [low, high])
            result = np.apply_along_axis(my_func, 0, result)
        return result

    def produce_range(self, *params):
        if self.type_selected_mode == 'Int':
            result = self.int_random_range(*params)
        else:
            result = self.float_random_range(*params)

        if self.as_list:
            result = result.tolist()

        return result

    def process(self):
        inputs = self.inputs
        outputs = self.outputs
        m = self.type_selected_mode
        if outputs['Value'].is_linked:
            if m == 'Int':
                params = [inputs[i].sv_get()[0] for i in range(4)]
                if self.weighted and inputs[4].is_linked:
                    params.append(inputs[4].sv_get())
            elif m == 'Float':
                params = [inputs[i].sv_get()[0] for i in range(len(inputs)) if not inputs[i].hide]
            out = [self.produce_range(*args) for args in zip(*match_long_repeat(params))]
            outputs['Value'].sv_set(out)


def register():
    bpy.utils.register_class(SvRndNumGen)


def unregister():
    bpy.utils.unregister_class(SvRndNumGen)
