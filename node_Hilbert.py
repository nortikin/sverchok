import bpy
from node_s import *
from util import *
from types import *

class HilbertNode(Node, SverchCustomTreeNode):
    ''' Hilbert line '''
    bl_idname = 'HilbertNode'
    bl_label = 'Hilbert'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    level_ = bpy.props.IntProperty(name = 'level', description='Level', default=2, min=1, max=6, options={'ANIMATABLE'}, update=updateNode)
    size_ = bpy.props.FloatProperty(name = 'size', description='Size', default=1.0, min=0.1, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Level", "Level")
        self.inputs.new('StringsSocket', "Size", "Size")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "level_", text="Level")
        layout.prop(self, "size_", text="Size")

    def update(self):
        # inputs
        if len(self.outputs['Edges'].links)>0 or len(self.outputs['Vertices'].links)>0:
            if len(self.inputs['Level'].links)>0:
                if not self.inputs['Level'].node.socket_value_update:
                    self.inputs['Level'].node.update()
                Integer = int(eval(self.inputs['Level'].links[0].from_socket.StringsProperty)[0][0])
            else:
                Integer = self.level_
    
            if len(self.inputs['Size'].links)>0:
                if not self.inputs['Size'].node.socket_value_update:
                    self.inputs['Size'].node.update()
                Step = eval(self.inputs['Size'].links[0].from_socket.StringsProperty)[0][0]
            else:
                Step = self.size_
            

        # outputs
        if len(self.outputs['Vertices'].links)>0:
            if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
                if not self.outputs['Vertices'].node.socket_value_update:
                    self.outputs['Vertices'].node.update()
                
                verts = self.hilbert(0.0, 0.0, Step*1.0, 0.0, 0.0, Step*1.0, Integer)
                
                self.outputs['Vertices'].VerticesProperty = str([verts])
    
            if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
                if not self.outputs['Edges'].node.socket_value_update:
                    self.outputs['Edges'].node.update()
    
                listEdg = []
                r = len(verts)-1
                for i in range(r):
                    listEdg.append((i, i+1))
    
                edg = list(listEdg)
                self.outputs['Edges'].StringsProperty = str([edg])

    def hilbert(self, x0, y0, xi, xj, yi, yj, n):
        out = []
        if n <= 0:
            X = x0 + (xi + yi)/2
            Y = y0 + (xj + yj)/2
            out.append(X)
            out.append(Y)
            out.append(0)
            return [out]
            
        else:
            out.extend(self.hilbert(x0,               y0,               yi/2, yj/2, xi/2, xj/2, n - 1))
            out.extend(self.hilbert(x0 + xi/2,        y0 + xj/2,        xi/2, xj/2, yi/2, yj/2, n - 1))
            out.extend(self.hilbert(x0 + xi/2 + yi/2, y0 + xj/2 + yj/2, xi/2, xj/2, yi/2, yj/2, n - 1))
            out.extend(self.hilbert(x0 + xi/2 + yi,   y0 + xj/2 + yj,  -yi/2,-yj/2,-xi/2,-xj/2, n - 1))
            return out

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(HilbertNode)
    
def unregister():
    bpy.utils.unregister_class(HilbertNode)

if __name__ == "__main__":
    register()