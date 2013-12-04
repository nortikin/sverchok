import bpy
from node_s import *
from util import *
from types import *

class LineNode(Node, SverchCustomTreeNode):
    ''' Line '''
    bl_idname = 'LineNode'
    bl_label = 'Line'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_ = bpy.props.IntProperty(name = 'int_', description='Nº Vertices', default=2, min=2, options={'ANIMATABLE'}, update=updateNode)
    step_ = bpy.props.FloatProperty(name = 'step_', description='Step length', default=1.0, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices", "Nº Vertices")
        self.inputs.new('StringsSocket', "Step", "Step length")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "int_", text="Nº Vert")
        layout.prop(self, "step_", text="Step")

    def update(self):
        # inputs
        if len(self.inputs['Nº Vertices'].links)>0:
            if not self.inputs['Nº Vertices'].node.socket_value_update:
                self.inputs['Nº Vertices'].node.update()
            Integer = int(eval(self.inputs['Nº Vertices'].links[0].from_socket.StringsProperty)[0][0])
        else:
            Integer = self.int_

        if len(self.inputs['Step'].links)>0:
            if not self.inputs['Step'].node.socket_value_update:
                self.inputs['Step'].node.update()
            Step = eval(self.inputs['Step'].links[0].from_socket.StringsProperty)[0]
            
            if len(Step) < Integer:
                self.fullList(Step, Integer)
            
            listVert = []
            for i in range(Integer):
                listVert.append(round((i*Step[i]),4))
            X = listVert

        else:
            Step = self.step_
            listVert = [Step*(i) for i in range(Integer)]
            X = listVert

        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.outputs['Vertices'].node.update()


            Y = [0.0]
            Z = [0.0]
            max_num = len(X)
            self.fullList(Y,max_num)
            self.fullList(Z,max_num)

            points = list(zip(X,Y,Z))
            self.outputs['Vertices'].VerticesProperty = str([points])

        if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
            if not self.outputs['Edges'].node.socket_value_update:
                self.outputs['Edges'].node.update()

            listEdg = []
            for i in range(Integer-1):
                listEdg.append((i, i+1))

            edg = list(listEdg)
            self.outputs['Edges'].StringsProperty = str([edg])

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(LineNode)
    
def unregister():
    bpy.utils.unregister_class(LineNode)

if __name__ == "__main__":
    register()