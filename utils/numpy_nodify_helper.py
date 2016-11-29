# numpy_nodify_helper.py

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
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import (updateNode, enum_item as e)
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, BoolProperty, EnumProperty
)

node_details = {}


def make_ugen_class(name):
    generated_classname = "SvNP" + name
    return type(generated_classname, (SvNumpyBaseNode,), node_details[name])


class SvNumpyBaseNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = ""
    bl_label = ""

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'sig')
        layout.prop(self, 'info')


kind_dict = {
    '=>': ['Socket In', 'Prop'], 
    '>': ['Socket In'],
    '==': ['Prop'],
    '<': ['Socket Out'], 
    '<=': ['Socket Out', 'Prop']
}


def parse_cleaned_elements(cleaned_elements):
    num_elements = len(cleaned_elements)
    _ui_info = None
    if num_elements == 3:
        _name, _type, _prop_args = cleaned_elements
    elif num_elements == 4:
        _name, _type, _prop_args, _ui_info = cleaned_elements
    return _name, _type, _prop_args, _ui_info


def inject_attrs(name, descriptor, temp_dict):
    print('adding', name, 'to tempdict')

    lines = descriptor.strip().split('\n')
    ui_info = []
    props = {}
    sockets = []
    for item in lines:
        clean_line = item.strip()
        if not clean_line:
            continue
        kind = clean_line[:2].strip()
        elements = clean_line[3:].strip().split(',')
        element_types = kind_dict.get(kind)
        # print(element_types)

        cleaned_elements = [s.strip() for s in elements]
        _name, _type, _prop_args, _ui_info = parse_cleaned_elements(cleaned_elements)

        if 'Prop' in element_types:

            f = ''
            if _type in {'scalar', 'int'}:
                f = eval("IntProperty(" + str(_prop_args) + ', update=updateNode)')
            elif _type in {'float'}:
                f = eval("FloatProperty(" + str(_prop_args) + ', update=updateNode)')
            elif _type in {'bool'}:
                f = eval("BoolProperty(" + str(_prop_args) + ', update=updateNode)')
            else:
                print('failed', cleaned_elements)

            props[_name] = f

        g = ""
        if 'Socket In' in element_types:
            g = "    self.inputs.new('StringsSocket', '{0}')".format(_name)
            if 'Prop' in element_types:
                g += ".prop_name = '{0}'".format(_name)
        elif 'Socket Out' in element_types:
            g = "    self.outputs.new('StringsSocket', '{0}')".format(_name)
        if g:
            sockets.append(g)

    
    temp_dict['sv_doc'] = StringProperty(default=descriptor)
    temp_dict.update(props)

    if 'sv_init' in temp_dict:
        print('skipped auto generate sv_init')
    else:
        if sockets:
            sockets.insert(0, 'def sv_init(self, context):')
            sock_string = '\n'.join(sockets)
            exec(sock_string)
            temp_dict['sv_init'] = locals()['sv_init']

    if 'draw_buttons' in temp_dict:
        print('skipped auto generate draw_buttons')



def augment_node_dict(name, extend_dict):
    node_details[name] = {"bl_idname": "SvNP" + name, "bl_label": name.title()}
    node_details[name].update(extend_dict)

def generate_classes():
    return [make_ugen_class(name) for name in node_details.keys()]

def register_multiple(classes):
    _ = [bpy.utils.register_class(name) for name in classes]

def unregister_multiple(classes):
    _ = [bpy.utils.unregister_class(name) for name in classes]


def all_linked(*sockets):
    return all([s.is_linked for s in sockets])
