# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import bpy
# import mathutils
# from mathutils import Vector
from bpy.props import FloatProperty, EnumProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvSmoothLines(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: smooth lines fil 
    Tooltip: accepts seq of verts and weights, returns smoothed lines
    
    This node should accept verts and weights and return the smoothed line representation.
    """

    bl_idname = 'SvSmoothLines'
    bl_label = 'Smooth Lines'
    bl_icon = 'GREASEPENCIL'

    smooth_mode_options = [(k, k, '', i) for i, k in enumerate(["absolute", "relative"])]
    smooth_selected_mode = EnumProperty(
        items=smooth_mode_options, description="offers....",
        default="absolute", update=updateNode)

    close_mode_options = [(k, k, '', i) for i, k in enumerate(["cyclic", "open"])]
    close_selected_mode = EnumProperty(
        items=close_mode_options, description="offers....",
        default="cyclic", update=updateNode)


    weights = FloatProperty(default=0.0, name="weights", min=0)

    def sv_init(self, context):
        self.inputs.new("VerticesSocket", "vectors")
        self.inputs.new("StringsSocket", "weights").prop_name = "weights"
        self.inputs.new("StringsSocket", "attributes")

    # def draw_buttons(self, context, layout):
    #    ...

    def process(self):
        necessary_sockets = [self.inputs["vectors"], self.inputs["weights"]]
        if not all(s.is_linked for s in necessary_sockets):
            return

        if self.inputs["attributes"].is_linked:
            # gather own data, rather than socket data

        


def register():
    bpy.utils.register_class(SvSmoothLines)


def unregister():
    bpy.utils.unregister_class(SvSmoothLines)