import bpy
from node_s import *
from util import *
from bpy.props import BoolProperty, FloatProperty

class SvMapRangeNode(Node, SverchCustomTreeNode):
    ''' Map a range from one to another'''
    bl_idname = 'SvMapRangeNode'
    bl_label = 'Map Range'
    bl_icon = 'OUTLINER_OB_EMPTY'

    old_min = FloatProperty(
        name='Old Min', description='Old Min', default=0,
        options={'ANIMATABLE'}, update=updateNode)

    old_max = FloatProperty(
        name='Old Max', description='Old Max', default=1,
        options={'ANIMATABLE'}, update=updateNode)
    
    new_min = FloatProperty(
        name='New Min', description='New Min', default=0,
        options={'ANIMATABLE'}, update=updateNode)

    new_max = FloatProperty(
        name='New Max', description='New Max', default=10,
        options={'ANIMATABLE'}, update=updateNode)
    
    value = FloatProperty(
        name='Value', description='New Max', default=.5,
        options={'ANIMATABLE'}, update=updateNode)
    
    clamp = BoolProperty(default=True,name='Clamp',update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Value").prop_name = 'value'
        self.inputs.new('StringsSocket', "Old Min").prop_name = 'old_min'
        self.inputs.new('StringsSocket', "Old Max").prop_name = 'old_max'
        self.inputs.new('StringsSocket', "New Min").prop_name = 'new_min'
        self.inputs.new('StringsSocket', "New Max").prop_name = 'new_max'

        self.outputs.new('StringsSocket', "Value")

    def draw_buttons(self, context, layout):
        layout.prop(self, "clamp")
    
    def map_range(self,x_list,old_min,old_max,new_min,new_max):
        old_d = old_max - old_min
        new_d = new_max - new_min
        scale = new_d/old_d
        
        def f(x):
            return new_min + (x-old_min)*scale
            
        if self.clamp:
            return [min(new_max,max(new_min,f(x))) for x in x_list]
        else:
            return [f(x) for x in x_list]
            
    def update(self):
        inputs = self.inputs
        outputs = self.outputs

        # outputs, end early.
        if not 'Value' in outputs or not outputs['Value'].links:
            return
        value_in=iter(inputs[0].sv_get())
        param=[repeat_last(inputs[i].sv_get()[0]) for i in range(1,5)]
        out = [self.map_range(*args) for args in zip(value_in, *param)]
        self.outputs['Value'].sv_set(out)
                
                
def register():
    bpy.utils.register_class(SvMapRangeNode)

def unregister():
    bpy.utils.unregister_class(SvMapRangeNode)
