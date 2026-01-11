import bpy
import sverchok

class SvSimpleTextNode(bpy.types.Node, sverchok.node_tree.SverchCustomTreeNode):
    """
    Triggers: Text string
    Tooltip: simple text
    """
    bl_idname = 'SvSimpleTextNode'
    bl_label = 'Simple Text'
    bl_icon = 'FILE_TEXT'
    replacement_nodes = [('SvSimpleTextNodeMK2', None, None)] 
    
    def sv_init(self, context):
        item = self.outputs.new('SvTextSocket', "Text")
        item.custom_draw = "draw_output"
    
    def draw_output(self, socket, context, layout):
        row = layout.row(align=True)
        row.prop(socket, "default_property", text="")

    def process(self):
        text_socket = self.outputs[0]
        text_socket.sv_set([[text_socket.default_property]])
    

classes = [SvSimpleTextNode]
register, unregister = bpy.utils.register_classes_factory(classes)
