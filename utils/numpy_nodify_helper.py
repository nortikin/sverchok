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


node_details = {}

def make_ugen_class(name, node_details):
    generated_classname = "SvNP" + name
    return type(generated_classname, (SvNumpyBaseNode,), node_details[name])


class SvNumpyBaseNode(bpy.types.Node, SverchCustomTreeNode):
    bl_idname = ""
    bl_label = ""
    
    def draw_buttons(self, context, layout):
        layout.prop(self, 'sig')

    def draw_buttons_ext(self, context, layout):
        layout.prop(self, 'sig')
        layout.prop(self, 'info')



def augment_node_dict(name, extend_dict):
    node_details[name] = {"bl_idname": "SvNP" + name, "bl_label": name.title()}
    node_details[name].update(extend_dict)

def generate_classes(node_details):
    return [make_ugen_class(name, node_details) for name in node_details.keys()]

def register_multiple(classes):
    _ = [bpy.utils.register_class(name) for name in classes]

def unregister_multiple(classes):
    _ = [bpy.utils.unregister_class(name) for name in classes]


def all_linked(*sockets):
    return all([s.is_linked for s in sockets])