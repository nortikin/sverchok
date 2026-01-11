import bpy
import sverchok
# Modification date 2026.01.06: Added imports for updateNode and Show3DProperties
from sverchok.data_structure import updateNode
from sverchok.utils.nodes_mixins.show_3d_properties import Show3DProperties

class SvSimpleTextNodeMK2(Show3DProperties, bpy.types.Node, sverchok.node_tree.SverchCustomTreeNode):
    """
    Triggers: Text string
    Tooltip: simple text
    """
    bl_idname = 'SvSimpleTextNodeMK2'
    bl_label = 'Simple Text'
    bl_icon = 'FILE_TEXT'

    # Modification date 2026.01.06: text_prop defined with empty default value
    text_prop: bpy.props.StringProperty(
        name="Text", 
        default="", 
        update=updateNode
    )
    
    def sv_init(self, context):
        # Modification date 2026.01.06: Using SvStringsSocket for standard string handling
        self.inputs.new('SvStringsSocket', "Text").prop_name = 'text_prop'
        self.outputs.new('SvStringsSocket', "Text")
    
    def draw_buttons_ext(self, context, layout):
        layout.prop(self, "draw_3dpanel", icon="PLUGIN", text="Show in 3D Panel")

    # Modification date 2026.01.06: Refined 3D Panel UI to maintain "Label: Value" format even when linked
    def draw_buttons_3dpanel(self, layout):
        node_label = self.label if self.label else self.name
        show_editable_prop = True
        
        if self.inputs[0].is_linked:
            try:
                in_data = self.inputs[0].sv_get()
                # Modification date 2026.01.06: Check if input data is not empty [] or [[]]
                if in_data and in_data[0]:
                    # Estraiamo il testo dalla struttura nidificata [[testo]]
                    display_text = str(in_data[0][0]) if in_data[0] else ""
                    layout.label(text=f"{node_label}: {display_text}")
                    show_editable_prop = False
            except:
                layout.label(text=f"{node_label}: <Data pending>")
                show_editable_prop = False
        
        # Modification date 2026.01.06: Show editable property if not linked or if linked data is empty
        if show_editable_prop:
            layout.prop(self, "text_prop", text=node_label)

    def process(self):
        # Modification date 2026.01.06: Process logic to output either local property or incoming socket data
        # Modification date 2026.01.06: Fallback to text_prop if input is linked but receives empty list [] or [[]]
        if self.inputs[0].is_linked:
            in_data = self.inputs[0].sv_get()
            if in_data and in_data[0]:
                self.outputs[0].sv_set(in_data)
                return

        self.outputs[0].sv_set([[self.text_prop]])
    

classes = [SvSimpleTextNodeMK2]
register, unregister = bpy.utils.register_classes_factory(classes)
if __name__ == '__main__': register()