import bpy
from node_s import *

class GenSeriesNode(Node, SverchCustomTreeNode):
    ''' Generator series '''
    bl_idname = 'GenSeriesNode'
    bl_label = 'List Series'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('NodeSocketFloat', "Start", "Start").default_value = 0
        self.inputs.new('NodeSocketFloat', "Stop", "Stop").default_value = 10
        self.inputs.new('NodeSocketFloat', "Step", "Step").default_value = 2
        self.outputs.new('StringsSocket', "Series", "Series")
        

    def update(self):
        # inputs
        if 'Start' in self.inputs and len(self.inputs['Start'].links)>0 and type(self.inputs['Start'].links[0].from_socket) == bpy.types.NodeSocketFloat:
            if not self.inputs['Start'].node.socket_value_update:
                self.inputs['Start'].node.update()
            Start = self.inputs['Start'].links[0].from_socket.default_value
        else:
            Start = self.inputs['Start'].default_value
    
        if 'Stop' in self.inputs and len(self.inputs['Stop'].links)>0 and type(self.inputs['Stop'].links[0].from_socket) == bpy.types.NodeSocketFloat:
            if not self.inputs['Stop'].node.socket_value_update:
                self.inputs['Stop'].node.update()
            Stop = self.inputs['Stop'].links[0].from_socket.default_value
        else:
            Stop = self.inputs['Stop'].default_value
        
        if 'Step' in self.inputs and len(self.inputs['Step'].links)>0 and type(self.inputs['Step'].links[0].from_socket) == bpy.types.NodeSocketFloat:
            if not self.inputs['Step'].node.socket_value_update:
                self.inputs['Step'].node.update()
            Step = self.inputs['Step'].links[0].from_socket.default_value
        else:
            Step = self.inputs['Step'].default_value
        
        # outputs
        if 'Series' in self.outputs and len(self.outputs['Series'].links)>0:
            if not self.outputs['Series'].node.socket_value_update:
                self.inputs['Series'].node.update()
            #print (Start, Stop, Step)
            series = [c for c in self.xfrange(Start, Stop, Step)]
            
            self.outputs['Series'].StringsProperty = str([series, ])

    def xfrange(self, start, stop, step):
        while start < stop:
            yield start
            start += step
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(GenSeriesNode)
    
def unregister():
    bpy.utils.unregister_class(GenSeriesNode)

if __name__ == "__main__":
    register()