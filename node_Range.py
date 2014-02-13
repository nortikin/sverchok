import bpy
from node_s import *
from util import *

class GenRangeNode(Node, SverchCustomTreeNode):
    ''' Generator: Range '''
    bl_idname = 'GenRangeNode'
    bl_label = 'List Range'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    start_ = bpy.props.FloatProperty(name = 'start', description='start', default=0, options={'ANIMATABLE'}, update=updateNode)
    stop_ = bpy.props.FloatProperty(name = 'stop', description='stop', default=1, options={'ANIMATABLE'}, update=updateNode)
    divisions_ = bpy.props.IntProperty(name = 'divisions', description='divisions', default=10, min=2, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Start", "Start")
        self.inputs.new('StringsSocket', "Stop", "Stop")
        self.inputs.new('StringsSocket', "Divisions", "Divisons")
        self.outputs.new('StringsSocket', "Range", "Range")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "start_", text="start")
        layout.prop(self, "stop_", text="stop")
        layout.prop(self, "divisions_", text="divisons")

    def update(self):
        # inputs
        if 'Start' in self.inputs and self.inputs['Start'].links:
            tmp = SvGetSocketAnyType(self,self.inputs['Start'])
            Start = tmp[0][0]
        else:
            Start = self.start_
    
        if 'Stop' in self.inputs and self.inputs['Stop'].links:
            tmp = SvGetSocketAnyType(self,self.inputs['Stop'])
            Stop = tmp[0][0]
        else:
            Stop = self.stop_
        
        if 'Divisions' in self.inputs and self.inputs['Divisions'].links:
            tmp = SvGetSocketAnyType(self,self.inputs['Divisions'])
            Divisions = tmp[0][0]
        else:
            Divisions = self.divisions_
        
        # outputs
        if 'Range' in self.outputs and self.outputs['Range'].links:
            if Divisions < 2:
                Divisions = 2
            Range = [Start]
            if Divisions > 2:
                Range.extend([c for c in self.xfrange(Start, Stop, Divisions)])                       
            Range.append(Stop)
            SvSetSocketAnyType(self, 'Range',[Range])

    def xfrange(self, start, stop, divisions):       
        step = (stop - start) / (divisions - 1 )
        count = start 
        for i in range( divisions - 2 ):
            count += step
            yield count
         
         
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(GenRangeNode)
    
def unregister():
    bpy.utils.unregister_class(GenRangeNode)

if __name__ == "__main__":
    register()
