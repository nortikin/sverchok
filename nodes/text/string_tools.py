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
from bpy.props import EnumProperty, IntProperty, BoolProperty, StringProperty

from sverchok.ui.sv_icons import custom_icon
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode, list_match_func, numpy_list_match_modes, levels_of_list_or_np
from sverchok.utils.sv_itertools import recurse_f_level_control
# pylint: disable=C0326

# Rules for modification:
#     1) Keep 4 items per column, 5 for socket labels
#     2) only add new function with unique number

def split(x, c, max_num):
    return x.split(c, max_num) if c else x.split(' ', max_num)

def join(x, add_breaks):
    print('add_breaks', add_breaks)
    if add_breaks[0]:
        return [''.join([l+'\n' for l in x])]
    else:
        return[''.join(x)]
def find_all(text, chars):
    out =[]
    index=0
    while index < len(text):
        f = text.find(chars, index, len(text))

        if f==-1:
            break
        else:
            out.append(f)
            index=f+1
    return out

def find_all_slice(text, chars, start, end):
    out =[]
    index=start
    while index < end+1:
        f = text.find(chars, index, end)

        if f==-1:
            break
        else:
            out.append(f)
            index=f+1
    return out

def number_to_string(data, precision):
    return ("{:." + str(precision) + "f}").format(float(data))

func_dict = {
    "---------------OPS" : "#---------------------------------------------------#",
    "to_string":  (0,   str,                                 ('t t'),    "To String"),
    "to_number":  (1,   eval,                                ('t s'),    "To Number"),
    "num_to_str": (3,   number_to_string ,                   ('ss t'),   "Number To String", ('Precision',)),
    "join":       (5,   lambda x, y: ''.join([x,y]),         ('tt t'),   "Join"),
    "join_all":   (6,   join,                                ('tb t'),   "Join All",         ('Add Break Lines',)),
    "split":      (10,  split,                               ('tcs t'),  "Split",            ('Spliter', 'Max Split')),
    "splitlines": (11,  lambda x,b: x.splitlines(b),         ('tb t'),   "Splitlines"),
    "partition":  (12,  lambda x, c: x.partition(c),         ('tc t'),   "Left Partition"),
    "rpartition": (13,  lambda x, c: x.rpartition(c),        ('tc t'),   "Right Partition"),
    "find_f_all": (20,  lambda x, c: x.find(c),              ('tc s'),   "Find First",       ('Character', 'Start', 'End')),
    "find_f_sli": (21,  lambda x, c, s, e: x.find(c, s, e),  ('tcsn s'), "Find First Slice", ('Character', 'Start', 'End')),
    "find_l_all": (22,  lambda x, c: x.rfind(c),             ('tc s'),   "Find Last",        ('Character', 'Start', 'End')),
    "find_l_sli": (23,  lambda x, c, s, e: x.rfind(c, s, e), ('tcsn s'), "Find Last Slice",  ('Character', 'Start', 'End')),
    "find_all":   (24,  find_all,                            ('tc s'),   "Find All",         ('Character', 'Start', 'End')),
    "find_all_sl":(25,  find_all_slice,                      ('tcsn s'), "Find All Slice",   ('Character', 'Start', 'End')),
    "count":      (30,  lambda x, c: x.count(c),             ('tt s'),   "Count"),
    "replace":    (40,  lambda x, c, c2, n: x.replace(c, c2, n),('tcds t'),  "Replace",          ('Find', 'Replace', 'Count')),

    "lower":      (50,  lambda x: x.lower(),                 ('t t'),    "Lower"),
    "upper":      (51,  lambda x: x.upper(),                 ('t t'),    "Upper"),
    "capitalize": (52,  lambda x : x.capitalize(),           ('t t'),    "Capitalize"),
    "title":      (53,  lambda x: x.title(),                 ('t t'),    "Title"),
    "casefold":   (54,  lambda x : x.casefold(),             ('t t'),    "Casefold"),
    "swapcase":   (55,  lambda x: x.swapcase(),              ('t t'),    "Swapcase"),

    "strip":      (60,  lambda x, c: x.strip(c),             ('tc t'),   "Strip"),
    "lstrip":     (61,  lambda x, c: x.lstrip(c),            ('tc t'),   "Left Strip"),
    "rstrip":     (62,  lambda x, c: x.rstrip(c),            ('tc t'),   "Right Strip"),
    "ljust":      (63,  lambda x, l, c: x.ljust(l, c),       ('tsc t'),  "Left Justify"),
    "center":     (64,  lambda x,l,c: x.center(l, c),        ('tst t'),  "Center",          ('Length', 'Character')),
    "rjust":      (65,  lambda x, l, c: x.rjust(l, c),       ('tsc t'),  "Right Justify"),
    "zfill":      (66,  lambda x,l: x.zfill(l),              ('ts t'),   "Zeros Fill"),

    "startswith": (70,  lambda x, c: x.startswith(c),        ('tc s'),   "Starts With"),
    "endswith":   (71,  lambda x, c: x.endswith(c),          ('tc s'),   "Ends With"),
    "isalnum":    (72,  lambda x: x.isalnum(),               ('t s'),    "Is Alphanumeric"),
    "isalpha":    (73,  lambda x: x.isalpha(),               ('t s'),    "Is Alphabetic"),
    "isdigit":    (74,  lambda x: x.isdigit(),               ('t s'),    "Is Digit"),
    "islower":    (75,  lambda x: x.islower(),               ('t s'),    "Is Lower"),
    "isspace":    (76,  lambda x: x.isspace(),               ('t s'),    "Is Space"),
    "istitle":    (77,  lambda x: x.istitle(),               ('t s'),    "Is Title"),
    "isupper":    (78,  lambda x: x.isupper(),               ('t s'),    "Is Upper"),

}


def func_from_mode(mode):
    return func_dict[mode][1]

def generate_node_items():
    prefilter = {k: v for k, v in func_dict.items() if not k.startswith('---')}
    return [(k, params[3], '', params[0]) for k, params in sorted(prefilter.items(), key=lambda k: k[1][0])]

mode_items = generate_node_items()

def string_tools(params, constant, matching_f):
    result = []
    func, inputs_signature = constant
    params = matching_f(params)
    for idx, signature in enumerate(inputs_signature):
        if signature in 'tcd' and type(params[idx][0]) != str:
            params[idx]=[str(p) for p in params[idx]]

    for props in zip(*params):
        result.append(func(*props))

    return result

class SvStringsToolsNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: Text modifier
    Tooltip: Strings operations as split, to uppecase, find characters...
    """

    bl_idname = 'SvStringsToolsNode'
    bl_label = 'Strings Tools'
    sv_icon = 'SV_SCALAR_MATH'

    def mode_change(self, context):
        self.update_sockets()
        updateNode(self, context)


    current_op: EnumProperty(
        name="Function", description="Function choice", default="join",
        items=mode_items, update=mode_change)

    xi_: IntProperty(default=1, name='x', update=updateNode)
    yi_: IntProperty(default=1, name='y', update=updateNode)


    list_match: EnumProperty(
        name="List Match",
        description="Behavior on different list lengths",
        items=numpy_list_match_modes, default="REPEAT",
        update=updateNode)
    level: IntProperty(
        name="Level",
        description="Level to convert to string",
        default=1,
        min=1,
        update=updateNode)

    text: StringProperty(
        name='Text',
        description='Text to modify',
        default='', update=updateNode)

    text2: StringProperty(
        name='Text',
        description='Text to modify',
        default='', update=updateNode)

    chars: StringProperty(
        name='Characters',
        description='Text to modify',
        default='', update=updateNode)

    chars2: StringProperty(
        name='Characters',
        description='Text to modify',
        default='', update=updateNode)
    keep_brakes:BoolProperty(
        name='Keep breaks',
        description='Text to modify',
        default=False, update=updateNode)

    sockets_signature: StringProperty(
        name='Characters',
        default='tt t',
        )

    def draw_label(self):
        label = [self.current_op]
        if self.hide:
            return " ".join(label).title()
        else:
            return str(self.bl_label)

    def draw_buttons(self, ctx, layout):
        row = layout.row(align=True)
        row.prop(self, "current_op", text="", icon_value=custom_icon("SV_FUNCTION"))
        if self.current_op == 'to_string':
            layout.prop(self,'level')

    def rclick_menu(self, context, layout):
        layout.prop_menu_enum(self, "current_op", text="Function")

    def sv_init(self, context):
        self.inputs.new('SvTextSocket', "Text").prop_name = 'text'
        self.inputs.new('SvTextSocket', "Text 2").prop_name = 'text2'
        for socket in self.inputs:
            socket.custom_draw = 'draw_prop_socket'
            socket.label = socket.name
        self.outputs.new('SvTextSocket', "Out")

    def draw_prop_socket(self, socket, context, layout):
        if socket.is_linked:
            layout.label(text=socket.label + f". {socket.objects_number or ''}")
        elif socket.prop_name:
            layout.prop(self, socket.prop_name, text=socket.label)
        else:
            layout.label(text=socket.label)

    def update_sockets(self):
        data =  func_dict.get(self.current_op)
        socket_info = func_dict.get(self.current_op)[2]
        if self.sockets_signature == socket_info:
            return
        t_inputs, t_outputs = socket_info.split(' ')
        old_inputs, old_outputs = self.sockets_signature.split(' ')
        self.sockets_signature = socket_info
        for s in range(len(self.inputs[1:])):
            self.inputs.remove(self.inputs[-1])
        for idx, s in enumerate(t_inputs[1:]):
            if s=="t":
                socket = self.inputs.new('SvTextSocket', 'Text 2')
                socket.prop_name = 'text2'
            elif s=="c":
                socket = self.inputs.new('SvTextSocket', 'Characters')
                socket.prop_name = 'chars'
            elif s=="d":
                socket = self.inputs.new('SvTextSocket', 'Characters 2')
                socket.prop_name = 'chars2'
            elif s=="s":
                socket = self.inputs.new('SvStringsSocket', 'Number')
                socket.prop_name = 'xi_'

            elif s=="n":
                socket = self.inputs.new('SvStringsSocket', 'Number 2')
                socket.prop_name = 'yi_'
                socket.custom_draw = 'draw_prop_socket'
                socket.label = socket.name
            elif s=="b":
                socket = self.inputs.new('SvTextSocket', 'Keep Breaks')
                socket.prop_name = 'keep_brakes'
            socket.custom_draw = 'draw_prop_socket'
            if len(data)>4:
                print(data[4], idx)
                socket.label = data[4][idx]
            else:
                socket.label = socket.name

        if t_outputs != old_outputs:
            self.outputs.remove(self.outputs[0])
            if t_outputs == 't':
                self.outputs.new('SvTextSocket', "Out")
            else:
                self.outputs.new('SvStringsSocket', 'Out')

    def process(self):

        if self.outputs[0].is_linked:
            current_func = func_from_mode(self.current_op)
            params = [si.sv_get(default=[[]], deepcopy=False) for si in self.inputs]
            matching_f = list_match_func[self.list_match]
            desired_levels = [2 if self.current_op=='join_all' else 1]*len(params)
            inputs_signature = self.sockets_signature.split(' ')[0]
            ops = [current_func, inputs_signature]
            if self.current_op  == 'to_string':
                depth = levels_of_list_or_np(params[0])
                desired_levels= [max(depth-self.level + 1, 1)]
            result = recurse_f_level_control(params, ops, string_tools, matching_f, desired_levels)

            self.outputs[0].sv_set(result)

classes = [SvStringsToolsNode]
register, unregister = bpy.utils.register_classes_factory(classes)
