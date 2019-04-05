import bpy
from bpy.props import (StringProperty, IntProperty, FloatProperty, BoolProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvMatlLinkSampler(bpy.types.Node, SverchCustomTreeNode):
    ''' Material Link Sampler '''
    bl_idname = 'SvMatlLinkSampler'
    bl_label = 'Material Link Curve Sampler'
    bl_icon = 'OUTLINER_OB_EMPTY'

    name_matl = StringProperty(name='name_matl', description='Name of the material with a RGB Curves or ColorRamp node', default='', update=updateNode)
    name_node = StringProperty(name='name_node', description='Node name (must be a "RGB Curves" or "ColorRamp" node)', default='RGB Curves', update=updateNode)

    count_c = IntProperty(name='C Count', options={'ANIMATABLE'}, description='Number of samples for C channel', default=10, min=2, max=9999, update=updateNode)
    count_r = IntProperty(name='R Count', options={'ANIMATABLE'}, description='Number of samples for R channel', default=10, min=2, max=9999, update=updateNode)
    count_g = IntProperty(name='G Count', options={'ANIMATABLE'}, description='Number of samples for G channel', default=10, min=2, max=9999, update=updateNode)
    count_b = IntProperty(name='B Count', options={'ANIMATABLE'}, description='Number of samples for B channel', default=10, min=2, max=9999, update=updateNode)

    refresh = BoolProperty(name='Refresh', description='Change this check after changing curves to refresh generated values', default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new('StringsSocket', "C Count").prop_name = 'count_c'
        self.inputs.new('StringsSocket', "R Count").prop_name = 'count_r'
        self.inputs.new('StringsSocket', "G Count").prop_name = 'count_g'
        self.inputs.new('StringsSocket', "B Count").prop_name = 'count_b'
        self.outputs.new('StringsSocket', "C", "C")
        self.outputs.new('StringsSocket', "R", "R")
        self.outputs.new('StringsSocket', "G", "G")
        self.outputs.new('StringsSocket', "B", "B")

    def draw_buttons(self, context, layout):    	
        layout.prop_search(self, "name_matl", bpy.data, 'materials', text="Material")
        layout.prop(self, "name_node", text="Node")
        layout.prop(self, "refresh", text="Change this to refresh")

        # get node from material 
        matl = bpy.data.materials[self.name_matl]
        if (matl):
            mnode = matl.node_tree.nodes[self.name_node]
            if type(mnode) is bpy.types.ShaderNodeRGBCurve:
                layout.template_curve_mapping(mnode, "mapping", type="COLOR")
            if type(mnode) is bpy.types.ShaderNodeValToRGB:
                layout.template_color_ramp(mnode, "color_ramp", expand=False)

    def get_rgb_curve_values(self, mnode, output_index, output_count, curve_index):
        output = self.outputs[output_index]
        if output.is_linked:
            data_out = []
            for i in range(0, output_count):
                data_out.append(mnode.mapping.curves[curve_index].evaluate(i / (output_count-1)))
            output.sv_set([data_out])

    def get_color_ramp_values(self, mnode, output_index, output_count, curve_index):
        output = self.outputs[output_index]
        if output.is_linked:
            data_out = []
            for i in range(0, output_count):
                data_out.append(mnode.color_ramp.evaluate(i / (output_count-1))[curve_index])
            output.sv_set([data_out])            

    def process(self):

        # channel mapping (C = 3, R = 0, G = 1, B = 2)
        chan_mapping = [3, 0, 1, 2]

        # get material node
        mnode = bpy.data.materials[self.name_matl].node_tree.nodes[self.name_node]

        # RGB Curves ?
        if type(mnode) is bpy.types.ShaderNodeRGBCurve:
            # init mapping
            mnode.mapping.initialize()
            # get values            
            for i in range(0, 4):
                self.get_rgb_curve_values(mnode, i, self.inputs[i].sv_get()[0][0], chan_mapping[i])

        # ColorRamp ?
        if type(mnode) is bpy.types.ShaderNodeValToRGB:
            # get values
            for i in range(0, 4):
                self.get_color_ramp_values(mnode, i, self.inputs[i].sv_get()[0][0], chan_mapping[i])            

def register():
    bpy.utils.register_class(SvMatlLinkSampler)

def unregister():
    bpy.utils.unregister_class(SvMatlLinkSampler)

if __name__ == '__main__':
    register() 
