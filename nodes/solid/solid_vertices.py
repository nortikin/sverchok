import bpy

from sverchok.node_tree import SverchCustomTreeNode


class SvSolidVerticesNode(SverchCustomTreeNode, bpy.types.Node):
    """
    Triggers: Solid Vertices
    Tooltip: Get Vertices from Solid
    """
    bl_idname = 'SvSolidVerticesNode'
    bl_label = 'Solid Vertices'
    bl_icon = 'VERTEXSEL'
    sv_category = "Solid Outputs"
    sv_dependencies = {'FreeCAD'}

    def sv_init(self, context):
        self.inputs.new('SvSolidSocket', "Solid")
        self.outputs.new('SvVerticesSocket', "Vertices")

    def process(self):
        if not any(socket.is_linked for socket in self.outputs):
            return

        solids = self.inputs[0].sv_get()

        verts_out = []
        verts_add = verts_out.append
        for solid in solids:
            verts = []
            for v in solid.Vertexes:
                verts.append(v.Point[:])

            verts_add(verts)

        self.outputs['Vertices'].sv_set(verts_out)


def register():
    bpy.utils.register_class(SvSolidVerticesNode)


def unregister():
    bpy.utils.unregister_class(SvSolidVerticesNode)
