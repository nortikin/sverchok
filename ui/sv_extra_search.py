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

import os
import importlib.util as getutil
import re

import bpy
from bpy.props import StringProperty

import sverchok
from sverchok.utils.sv_logging import sv_logger
from sverchok.utils.docstring import SvDocstring
from sverchok.utils.sv_default_macros import macros, DefaultMacros
from sverchok.ui.nodeview_space_menu import get_add_node_menu


addon_name = sverchok.__name__

loop = {}
loop_reverse = {}
local_macros = {}
ddir = lambda content: [n for n in dir(content) if not n.startswith('__')]


def format_item(k, v):
    return k + " | " + v['display_name']

def format_macro_item(k, v):
    return '< ' + k.replace('_', ' ') + " | " + slice_docstring(v)

def slice_docstring(desc):
    return SvDocstring(desc).get_shorthand()

def ensure_short_description(description):
    '''  the font is not fixed width, it makes little sense to calculate chars '''
    hardcoded_maxlen = 20
    if description:
        if len(description) > hardcoded_maxlen:
            description = description[:hardcoded_maxlen]
        description = ' | ' + description
    return description

def ensure_valid_show_string(nodetype):

    try:
        loop_reverse[nodetype.bl_label] = nodetype.bl_idname
        description = nodetype.bl_rna.docstring.get_shorthand()
        return nodetype.bl_label + ensure_short_description(description)
    except Exception as err:
        sv_logger.error(f'Nodetype "{nodetype}": ensure_valid_show_string() threw an exception:\n {err}')


def function_iterator(module_file):
    for name in ddir(module_file):
        obj = getattr(module_file, name)
        if callable(obj) and SvDocstring(obj.__doc__).has_shorthand():
            yield name, obj.__doc__

def get_main_macro_module(fullpath):
    if os.path.exists(fullpath):
        print('--- first time getting sv_macro_module --- ')
        spec = getutil.spec_from_file_location("macro_module.name", fullpath)
        macro_module = getutil.module_from_spec(spec)
        spec.loader.exec_module(macro_module)
        local_macros['sv_macro_module'] = macro_module
        return macro_module

def fx_extend(idx, datastorage):
    datafiles = os.path.join(bpy.utils.user_resource('DATAFILES', path='sverchok', create=True))
    fullpath = os.path.join(datafiles, 'user_macros', 'macros.py')

    # load from previous obtained module, else get from fullpath.
    macro_module = local_macros.get('sv_macro_module')
    if not macro_module:
        macro_module = get_main_macro_module(fullpath)
    if not macro_module:
        return

    for func_name, func_descriptor in function_iterator(macro_module):
        datastorage.append((func_name, format_macro_item(func_name, func_descriptor), '', idx))
        idx +=1


def gather_items(context):
    fx = []
    idx = 0

    for cat in get_add_node_menu().walk_categories():
        for item in cat:
            if not hasattr(item, 'bl_idname'):
                continue

            if item.bl_idname == 'NodeReroute':
                continue

            nodetype = bpy.types.Node.bl_rna_get_subclass_py(item.bl_idname)
            if not nodetype:
                continue

            docstring = ensure_valid_show_string(nodetype)
            if not docstring:
                continue

            fx.append((str(idx), docstring, '', idx))
            idx += 1

    for k, v in macros.items():
        fx.append((k, format_item(k, v), '', idx))
        idx += 1

    fx_extend(idx, fx)

    return fx


def item_cb(self, context):
    return loop.get('results') or [("A","A", '', 0),]


class SvExtraSearch(bpy.types.Operator):
    """ Extra Search library """
    bl_idname = "node.sv_extra_search"
    bl_label = "Extra Search"
    bl_property = "my_enum"

    my_enum: bpy.props.EnumProperty(items=item_cb)

    @classmethod
    def poll(cls, context):
        tree_type = getattr(context.space_data, 'tree_type', None)
        if tree_type in {'SverchCustomTreeType', }:
            return True

    def bl_idname_from_bl_label(self, context):
        macro_result = loop['results'][int(self.my_enum)]
        bl_label = macro_result[1].split(' | ')[0].strip()
        return loop_reverse[bl_label]

    def execute(self, context):
        # print(context.space_data.cursor_location)  (in nodeview space)
        # self.report({'INFO'}, "Selected: %s" % self.my_enum)
        if self.my_enum.isnumeric():
            macro_bl_idname = self.bl_idname_from_bl_label(self)
            DefaultMacros.ensure_nodetree(self, context)
            bpy.ops.node.sv_macro_interpreter(macro_bl_idname=macro_bl_idname)
        else:
            macro_reference = macros.get(self.my_enum)

            if macro_reference:
                handler, term = macro_reference.get('ident')
                getattr(DefaultMacros, handler)(self, context, term)

            elif hasattr(local_macros['sv_macro_module'], self.my_enum):
                func = getattr(local_macros['sv_macro_module'], self.my_enum)
                func(self, context)

        return {'FINISHED'}

    def invoke(self, context, event):
        context.space_data.cursor_location_from_region(event.mouse_region_x, event.mouse_region_y)
        
        if not loop.get('results'):
            loop['results'] = gather_items(context)
        
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def convert_string_to_settings(arguments):

    # expects       (varname=value,....)
    # for example   (selected_mode="int", fruits=20, alama=[0,0,0])
    def deform_args(**args):
        return args

    unsorted_dict = eval('deform_args{arguments}'.format(**vars()), locals(), locals())
    pattern = r'(\w+\s*)='
    results = re.findall(pattern, arguments)
    return [(varname, unsorted_dict[varname]) for varname in results]


class SvMacroInterpreter(bpy.types.Operator):
    """ Launch menu item as a macro """
    bl_idname = "node.sv_macro_interpreter"
    bl_label = "Sverchok check for new minor version"
    bl_options = {'REGISTER'}

    macro_bl_idname: StringProperty()
    settings: StringProperty()

    def create_node(self, context, node_type):
        space = context.space_data
        tree = space.edit_tree

        # select only the new node
        for n in tree.nodes:
            n.select = False

        node = tree.nodes.new(type=node_type)

        if self.settings:
            settings = convert_string_to_settings(self.settings)
            for name, value in settings:
                try:
                    setattr(node, name, value)
                except AttributeError as e:
                    self.report({'ERROR_INVALID_INPUT'}, "Node has no attribute " + name)
                    print(str(e))

        node.select = True
        tree.nodes.active = node
        node.location = space.cursor_location
        return node

    def execute(self, context):
        self.create_node(context, self.macro_bl_idname)
        bpy.ops.node.translate_attach_remove_on_cancel('INVOKE_DEFAULT')
        return {'FINISHED'}


classes = [SvExtraSearch, SvMacroInterpreter]


def register():
    for class_name in classes:
        bpy.utils.register_class(class_name)


def unregister():
    for class_name in reversed(classes):
        bpy.utils.unregister_class(class_name)
