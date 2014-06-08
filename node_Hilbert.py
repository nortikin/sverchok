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
        self.inputs.new('StringsSocket', "Level", "Level").prop_name='level_'
        self.inputs.new('StringsSocket', "Size", "Size").prop_name='size_'
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        pass
    
    def update(self):
        # inputs
        if 'Egdes' in self.outputs and self.outputs['Edges'].links or self.outputs['Vertices'].links:
            if self.inputs['Level'].links:
                Integer = int(SvGetSocketAnyType(self,self.inputs['Level'])[0][0])
            else:
                Integer = self.level_
    
            if self.inputs['Size'].links:
                Step = SvGetSocketAnyType(self,self.inputs['Size'])[0][0]
            else:
                Step = self.size_
            

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            verts = self.hilbert(0.0, 0.0, Step*1.0, 0.0, 0.0, Step*1.0, Integer)
            SvSetSocketAnyType(self,'Vertices',[verts])

        if 'Edges' in self.outputs and self.outputs['Edges'].links:
            listEdg = []
            r = len(verts)-1
            for i in range(r):
                listEdg.append((i, i+1))

            edg = list(listEdg)
            SvSetSocketAnyType(self,'Edges',[edg])

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

    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(HilbertNode)
    
def unregister():
    bpy.utils.unregister_class(HilbertNode)

if __name__ == "__main__":
    register()
