import bpy
from bpy.props import (StringProperty, IntProperty, FloatProperty, BoolProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvRGBCurvesLink(bpy.types.Node, SverchCustomTreeNode):
    ''' Custom Curves '''
    bl_idname = 'SvRGBCurvesLink'
    bl_label = 'RGB Curves Link'
    bl_icon = 'OUTLINER_OB_EMPTY'

    name_matl = StringProperty(name='name_matl', description='Name of the material with a RGB Curves node', default='', update=updateNode)
    name_node = StringProperty(name='name_node', description='Node name (must be a "RGB Curves" node)', default='RGB Curves', update=updateNode)

    list_len_c = IntProperty(name='C Length', options={'ANIMATABLE'}, description='Number of samples for C channel', default=10, min=2, max=9999, update=updateNode)
    list_len_r = IntProperty(name='R Length', options={'ANIMATABLE'}, description='Number of samples for R channel', default=10, min=2, max=9999, update=updateNode)
    list_len_g = IntProperty(name='G Length', options={'ANIMATABLE'}, description='Number of samples for G channel', default=10, min=2, max=9999, update=updateNode)
    list_len_b = IntProperty(name='B Length', options={'ANIMATABLE'}, description='Number of samples for B channel', default=10, min=2, max=9999, update=updateNode)

    scale_c = FloatProperty(name="C Scale", options={'ANIMATABLE'}, description='Multiplier for C', default=1.0, update=updateNode)
    scale_r = FloatProperty(name="R Scale", options={'ANIMATABLE'}, description='Multiplier for R', default=1.0, update=updateNode)
    scale_g = FloatProperty(name="G Scale", options={'ANIMATABLE'}, description='Multiplier for G', default=1.0, update=updateNode)
    scale_b = FloatProperty(name="B Scale", options={'ANIMATABLE'}, description='Multiplier for B', default=1.0, update=updateNode)

    offset_c = FloatProperty(name="C Offset", options={'ANIMATABLE'}, description='Offset for C', default=0.0, update=updateNode)
    offset_r = FloatProperty(name="R Offset", options={'ANIMATABLE'}, description='Offset for R', default=0.0, update=updateNode)
    offset_g = FloatProperty(name="G Offset", options={'ANIMATABLE'}, description='Offset for G', default=0.0, update=updateNode)
    offset_b = FloatProperty(name="B Offset", options={'ANIMATABLE'}, description='Offset for B', default=0.0, update=updateNode)

    refresh = BoolProperty(name='Refresh', description='Change this check after changing curves to refresh generated values', default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "C Length").prop_name = 'list_len_c'
        self.inputs.new('StringsSocket', "R Length").prop_name = 'list_len_r'
        self.inputs.new('StringsSocket', "G Length").prop_name = 'list_len_g'
        self.inputs.new('StringsSocket', "B Length").prop_name = 'list_len_b'
        self.inputs.new('StringsSocket', "C Scale").prop_name = 'scale_c'
        self.inputs.new('StringsSocket', "R Scale").prop_name = 'scale_r'
        self.inputs.new('StringsSocket', "G Scale").prop_name = 'scale_g'
        self.inputs.new('StringsSocket', "B Scale").prop_name = 'scale_b'        
        self.inputs.new('StringsSocket', "C Offset").prop_name = 'offset_c'
        self.inputs.new('StringsSocket', "R Offset").prop_name = 'offset_r'
        self.inputs.new('StringsSocket', "G Offset").prop_name = 'offset_g'
        self.inputs.new('StringsSocket', "B Offset").prop_name = 'offset_b'
        self.outputs.new('StringsSocket', "C", "C")
        self.outputs.new('StringsSocket', "R", "R")
        self.outputs.new('StringsSocket', "G", "G")
        self.outputs.new('StringsSocket', "B", "B")

    def draw_buttons(self, context, layout):    	
        layout.prop_search(self, "name_matl", bpy.data, 'materials', text="Material")
        layout.prop(self, "name_node", text="Node")
        layout.prop(self, "refresh", text="Refresh")

    def process(self):

        outputs = self.outputs
        list_len_c = self.inputs[0].sv_get()[0][0]
        list_len_r = self.inputs[1].sv_get()[0][0]
        list_len_g = self.inputs[2].sv_get()[0][0]
        list_len_b = self.inputs[3].sv_get()[0][0]
        scale_c = self.inputs[4].sv_get()[0][0]
        scale_r = self.inputs[5].sv_get()[0][0]
        scale_g = self.inputs[6].sv_get()[0][0]
        scale_b = self.inputs[7].sv_get()[0][0]
        offset_c = self.inputs[8].sv_get()[0][0]
        offset_r = self.inputs[9].sv_get()[0][0]
        offset_g = self.inputs[10].sv_get()[0][0]
        offset_b = self.inputs[11].sv_get()[0][0]

        shape = bpy.data.materials[self.name_matl].node_tree.nodes[self.name_node]
        shape.mapping.initialize()
        
        if outputs[0].is_linked:
            data_c = []
            for i in range(0, list_len_c):
                data_c.append(offset_c + (scale_c * shape.mapping.curves[3].evaluate(i / (list_len_c-1))))
            outputs[0].sv_set([data_c])

        if outputs[1].is_linked:
            data_r = []
            for i in range(0, list_len_r):
                data_r.append(offset_r + (scale_r * shape.mapping.curves[0].evaluate(i / (list_len_r-1))))
            outputs[1].sv_set([data_r])

        if outputs[2].is_linked:
            data_g = []
            for i in range(0, list_len_g):
                data_g.append(offset_g + (scale_g * shape.mapping.curves[1].evaluate(i / (list_len_g-1))))
            outputs[2].sv_set([data_g])

        if outputs[3].is_linked:
            data_b = []
            for i in range(0, list_len_b):
                data_b.append(offset_b + (scale_b * shape.mapping.curves[2].evaluate(i / (list_len_b-1))))
            outputs[3].sv_set([data_b])            

def register():
    bpy.utils.register_class(SvRGBCurvesLink)

def unregister():
    bpy.utils.unregister_class(SvRGBCurvesLink)

if __name__ == '__main__':
    register()