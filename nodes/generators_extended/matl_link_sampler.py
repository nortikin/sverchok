import bpy
from bpy.props import (StringProperty, IntProperty, FloatProperty, BoolProperty)
from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode

class SvMatlLinkSampler(bpy.types.Node, SverchCustomTreeNode):
    ''' Material Link Sampler '''
    bl_idname = 'SvMatlLinkSampler'
    bl_label = 'Material Link Sampler'
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
        layout.prop(self, "refresh", text="Refresh")

    def process(self):

        outputs = self.outputs
        count_c = self.inputs['C Count'].sv_get()[0][0]
        count_r = self.inputs['R Count'].sv_get()[0][0]
        count_g = self.inputs['G Count'].sv_get()[0][0]
        count_b = self.inputs['B Count'].sv_get()[0][0]

        # get material node
        mnode = bpy.data.materials[self.name_matl].node_tree.nodes[self.name_node]

        # RGB Curves ?
        if type(mnode) is bpy.types.ShaderNodeRGBCurve:
            # init mapping
            mnode.mapping.initialize()

            if outputs[0].is_linked:
                data_c = []
                for i in range(0, count_c):
                    data_c.append(mnode.mapping.curves[3].evaluate(i / (count_c-1)))
                outputs[0].sv_set([data_c])

            if outputs[1].is_linked:
                data_r = []
                for i in range(0, count_r):
                    data_r.append(mnode.mapping.curves[0].evaluate(i / (count_r-1)))
                outputs[1].sv_set([data_r])

            if outputs[2].is_linked:
                data_g = []
                for i in range(0, count_g):
                    data_g.append(mnode.mapping.curves[1].evaluate(i / (count_g-1)))
                outputs[2].sv_set([data_g])

            if outputs[3].is_linked:
                data_b = []
                for i in range(0, count_b):
                    data_b.append(mnode.mapping.curves[2].evaluate(i / (count_b-1)))
                outputs[3].sv_set([data_b])            

        # ColorRamp
        if type(mnode) is bpy.types.ShaderNodeValToRGB:

            if outputs[0].is_linked:
                data_c = []
                for i in range(0, count_c):
                    data_c.append(mnode.color_ramp.evaluate(i / (count_c-1))[3])
                outputs[0].sv_set([data_c])

            if outputs[1].is_linked:
                data_r = []
                for i in range(0, count_r):
                    data_r.append(mnode.color_ramp.evaluate(i / (count_r-1))[0])
                outputs[1].sv_set([data_r])

            if outputs[2].is_linked:
                data_g = []
                for i in range(0, count_g):
                    data_g.append(mnode.color_ramp.evaluate(i / (count_g-1))[1])
                outputs[2].sv_set([data_g])

            if outputs[3].is_linked:
                data_b = []
                for i in range(0, count_b):
                    data_b.append(mnode.color_ramp.evaluate(i / (count_b-1))[2])
                outputs[3].sv_set([data_b])

def register():
    bpy.utils.register_class(SvMatlLinkSampler)

def unregister():
    bpy.utils.unregister_class(SvMatlLinkSampler)

if __name__ == '__main__':
    register()