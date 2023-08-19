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

import ast
import traceback

import bpy
from bpy.props import StringProperty, BoolProperty, IntProperty, FloatProperty, FloatVectorProperty
from bpy.types import bpy_prop_array
import mathutils
from mathutils import Matrix, Vector, Euler, Quaternion, Color

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import Matrix_generate, updateNode, node_id
from sverchok.old_nodes.getprop import assign_data, get_object, apply_alias, parse_to_path, secondary_type_assesment, types

class SvSetPropNode(SverchCustomTreeNode, bpy.types.Node):
    ''' Set Property '''
    bl_idname = 'SvSetPropNode'
    bl_label = 'Set Property'
    bl_icon = 'FORCE_VORTEX'
    sv_icon = 'SV_PROP_SET'

    ok_prop: BoolProperty(default=False)
    bad_prop: BoolProperty(default=False)


    @property
    def obj(self):
        eval_str = apply_alias(self.prop_name)
        ast_path = ast.parse(eval_str)
        path = parse_to_path(ast_path.body[0].value)
        return get_object(path)
        
    def verify_prop(self, context):

        # test first 
        try:
            obj = self.obj
        except:
            traceback.print_exc()
            self.bad_prop = True
            return

        # execute second
        self.bad_prop = False

        s_type = types.get(type(self.obj))
        if not s_type:
            s_type = secondary_type_assesment(self.obj)

        p_name = {
            float: "float_prop", 
            int: "int_prop",
            bpy_prop_array: "color_prop"
        }.get(type(self.obj),"")
        
        inputs = self.inputs

        if inputs and s_type: 
            socket = inputs[0].replace_socket(s_type)
            socket.prop_name = p_name
        elif s_type:
            inputs.new(s_type, "Data").prop_name = p_name
        if s_type == "SvVerticesSocket":
            inputs[0].use_prop = True

        updateNode(self, context)

    def local_updateNode(self, context):
        # no further interaction with the nodetree is required.
        self.process()
        
    prop_name: StringProperty(name='', update=verify_prop)
    float_prop: FloatProperty(update=updateNode, name="x")
    int_prop: IntProperty(update=updateNode, name="x")
    color_prop: FloatVectorProperty(
        name="Color", description="Color", size=4,
        min=0.0, max=1.0, subtype='COLOR', update=local_updateNode)

    def draw_buttons(self, context, layout):
        layout.alert = self.bad_prop
        layout.prop(self, "prop_name", text="")

    def process(self):
        # print("<< Set process is called")
        data = self.inputs[0].sv_get()
        eval_str = apply_alias(self.prop_name)
        ast_path = ast.parse(eval_str)
        path = parse_to_path(ast_path.body[0].value)
        obj = get_object(path)

        if isinstance(obj, (int, float, bpy_prop_array)):
            obj = get_object(path[:-1])
            p_type, value = path[-1]
            if p_type == "attr":
                setattr(obj, value, data[0][0])
            else: 
                obj[value] = data[0][0]
        else:
            assign_data(obj, data)


def register():
    bpy.utils.register_class(SvSetPropNode)

def unregister():
    bpy.utils.unregister_class(SvSetPropNode)
