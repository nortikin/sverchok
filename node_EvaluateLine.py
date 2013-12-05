import bpy
from node_s import *
from util import *

class EvaluateLine(Node, SverchCustomTreeNode):
    ''' EvaluateLine '''
    bl_idname = 'EvaluateLineNode'
    bl_label = 'EvaluateLine'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    evaluate_ = bpy.props.FloatProperty(name = 'evaluate_', description='Step length', default=0.0, min=0.0, max=1.0, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertice A", "Vertice A")
        self.inputs.new('VerticesSocket', "Vertice B", "Vertice B")
        self.outputs.new('VerticesSocket', "EvPoint", "EvPoint")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "evaluate_", text="")

    def update(self):
        # inputs
        if len(self.inputs['Vertice A'].links)>0:
            if not self.inputs['Vertice A'].node.socket_value_update:
                self.inputs['Vertice A'].node.update()
            Vertices = eval(self.inputs['Vertice A'].links[0].from_socket.VerticesProperty)
            
            data1 = dataCorrect(Vertices)
            X1, Y1, Z1 = [], [], []

            for obj in data1:
                for item in obj:
                    Z1.append(item[2])
                    Y1.append(item[1])
                    X1.append(item[0])

        if len(self.inputs['Vertice B'].links)>0:
            if not self.inputs['Vertice B'].node.socket_value_update:
                self.inputs['Vertice B'].node.update()
            Edges = eval(self.inputs['Vertice B'].links[0].from_socket.VerticesProperty)

            data2 = dataCorrect(Edges) 
            X2, Y2, Z2 = [], [], []

            for obj in data2:
                for item in obj:
                    Z2.append(item[2])
                    Y2.append(item[1])
                    X2.append(item[0])

        # outputs
        if 'EvPoint' in self.outputs and len(self.outputs['EvPoint'].links)>0:
            if not self.outputs['EvPoint'].node.socket_value_update:
                self.outputs['EvPoint'].node.update()
            m = self.evaluate_
            a,b,c = [],[],[]
            for i, x in enumerate(X1):
                a.append(x+(X2[i]-x)*m)
                b.append(Y1[i]+(Y2[i]-Y1[i])*m)
                c.append(Z1[i]+(Z2[i]-Z1[i])*m)
            

            points = list(zip(a,b,c))
            self.outputs['EvPoint'].VerticesProperty = str([points])

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(EvaluateLine)
    
def unregister():
    bpy.utils.unregister_class(EvaluateLine)

if __name__ == "__main__":
    register()
