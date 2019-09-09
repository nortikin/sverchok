# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import ast

import bpy
from bpy.props import StringProperty, BoolProperty

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvTopologySimple(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: topo
    Tooltip: manually supply topolgy for simple meshes
    
    sometimes you want to just create a simple polygon or mesh

    The most simplified way to input a list of edges or faces (or both) is to 
    use "simplified mode" (default) with wrapping enabled. This mode lets you 
    create a single mesh output by writing

       (edges field)   0 1, 2 3, 4 5
       (faces field)   0 1 2, 2 3 4, 4 5 6
    
    that converts these strings automatically to proper python lists that sverchok
    well recognize as topology

        edges = [
                   [  [0,1],[2,3],[4,5]  ]
                ]
    
        faces = [
                   [  [0,1,2],[2,3,4],[4,5,6]  ]
                ]

    """

    bl_idname = 'SvTopologySimple'
    bl_label = 'Topology Simple'
    bl_icon = 'ALIGN_BOTTOM'

    prop_edges: StringProperty(default='', name='edges', update=updateNode)
    prop_faces: StringProperty(default='', name='faces', update=updateNode)
    simplified: BoolProperty(default=True, name="simplify input", update=updateNode)
    wrap: BoolProperty(default=True, name="wrap output", description="wraps outputs with a set of [  ]", update=updateNode)

    def sv_init(self, context):
        self.outputs.new("SvStringsSocket", "Edges")
        self.outputs.new("SvStringsSocket", "Faces")

    def draw_buttons(self, context, layout):
        layout.row().prop(self, "prop_edges", icon="EDGESEL", text="")
        layout.row().prop(self, "prop_faces", icon="FACESEL", text="")
        row = layout.row()
        row.prop(self, "simplified")
        row.prop(self, "wrap")

    def manipulate(self, socket):
        data = getattr(self, f"prop_{socket.name.lower()}")

        try:

            if self.simplified:
                data = data.split(',')
                data = [element.strip() for element in data]
                data = [element.split() for element in data]
                data = [[int(val) for val in element] for element in data]
            else:
                data = ast.literal_eval(data)
            
            if self.wrap:
                data = [data]

        except Exception as err:
            print(err)

        return data

    def process(self):
        for socket in self.outputs:
            if socket.is_linked:
                socket.sv_set(self.manipulate(socket))


def register():
    bpy.utils.register_class(SvTopologySimple)


def unregister():
    bpy.utils.unregister_class(SvTopologySimple)
