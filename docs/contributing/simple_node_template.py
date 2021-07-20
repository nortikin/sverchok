# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


import bpy
from mathutils import Vector
from bpy.props import FloatProperty
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode


class SvScaleVectorNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: vector multiply scale
    Tooltip: This node multiply vector and some value

    Merely for illustration of node creation workflow
    """
    bl_idname = 'SvScaleVectorNode'  # should be add to `sverchok/index.md` file
    bl_label = 'Name shown in menu'
    bl_icon = 'GREASEPENCIL'

    value: FloatProperty(  # https://docs.blender.org/api/current/bpy.props.html
        name="My value",
        default=2,
        update=updateNode
    )

    def sv_init(self, context):
        self.inputs.new('SvVerticesSocket', "Vertices")  # All socket types are in `sverchok/core/sockets.py` file
        self.outputs.new('SvVerticesSocket', "Vertices")

    def draw_buttons(self, context, layout):
        layout.prop(self, "value")  # https://docs.blender.org/api/current/bpy.types.UILayout.html

    def process(self):
        # read input value
        input_vertices = self.inputs["Vertices"].sv_get(default=[])

        # vectorization code
        output_vertices = []
        for in_vert_list in input_vertices:  # object level
            out_vert_list = []

            for v in in_vert_list:  # value level

                # perform the node function
                out_vert_list.append((Vector(v) * self.value)[:])

            output_vertices.append(out_vert_list)

        # wright output value
        self.outputs["Vertices"].sv_set(output_vertices)


def register():
    bpy.utils.register_class(SvScaleVectorNode)


def unregister():
    bpy.utils.unregister_class(SvScaleVectorNode)


# run this code in Blender text editor to create the node in a node tree
if __name__ == "__main__":
    cls = bpy.types.Node.bl_rna_get_subclass_py("SvScaleVectorNode")
    if cls:
        bpy.utils.unregister_class(cls)
    register()
    try:
        tree = next(t for t in bpy.data.node_groups if t.bl_idname == 'SverchCustomTreeType')
    except StopIteration:
        raise LookupError("You should create Sverchok tree first")
    else:
        tree.nodes.new(SvScaleVectorNode.bl_idname)
