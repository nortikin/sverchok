from node_s import *
from util import *
from operator import itemgetter
import bpy

# distance between two points without sqrt, for comp only
def distK(v1,v2):
    return sum((i[0]-i[1])**2 for i in zip(v1,v2))

class SvVertSortNode(Node, SverchCustomTreeNode):
    '''Vertices sort'''
    bl_idname = 'SvVertSortNode'
    bl_label = 'Vertices Sort'
    bl_icon = 'OUTLINER_OB_EMPTY'

    def mode_change(self,context):
        if self.mode=='XYZ':
            while len(self.inputs)>2:
                self.inputs.remove(self.inputs[-1])
        if self.mode=='DIST':
            while len(self.inputs)>2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('VerticesSocket', 'Base Point', 'Base Point')

        if self.mode=='AXIS':
            while len(self.inputs)>2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('VerticesSocket', 'Base Point', 'Base Point')
            self.inputs.new('VerticesSocket', 'Axis', 'Axis') 
        if self.mode=='USER':
            while len(self.inputs)>2:
                self.inputs.remove(self.inputs[-1])
            self.inputs.new('StringsSocket', 'Index Data', 'Index Data')
            

    modes = [("XYZ",    "XYZ", "X Y Z Sort",    1),
             ("DIST",   "Dist", "Distance",     2),
            # ("AXIS",   "Axis", "Axial sort",   3),
             ("USER",   "User", "User defined", 10)]

    mode = bpy.props.EnumProperty(items = modes, default='XYZ',update=mode_change)

    
    def draw_buttons(self,context,layout):
        layout.label("Sort mode:")
        layout.prop(self, "mode", expand = True)
        if self.mode=="XYZ":
            pass

    def init(self, context):
        self.inputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.inputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')

        self.outputs.new('VerticesSocket', 'Vertices', 'Vertices')
        self.outputs.new('StringsSocket', 'PolyEdge', 'PolyEdge')
        self.outputs.new('StringsSocket', 'Item order','Item Order')

    def update(self):

        if 'Vertices' in self.inputs and self.inputs['Vertices'].links and \
            'PolyEdge' in self.inputs and self.inputs['PolyEdge'].links:

            verts = SvGetSocketAnyType(self,self.inputs['Vertices'])
            poly_edge = SvGetSocketAnyType(self,self.inputs['PolyEdge'])
            verts_out = []
            poly_edge_out = []
            item_order = []
            
            if not 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                return
            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].links:
                polyOutput = True
            else:
                polyOutput = False
            if 'Item Order' in self.outputs and self.outputs['Item Order'].links:
                orderOutput = True
            else:
                orderOutput = False
                
            if self.mode=='XYZ':
                
                for v,p in zip(verts,poly_edge):
                    s_v=sorted(((e[0],e[1],e[2],i) for i,e in enumerate(v)),key=itemgetter(0,1,2),reverse=False)
                    
                    verts_out.append([v[:3] for v in s_v])
                    if polyOutput:
                        v_index = dict( zip((i[-1] for i in s_v), range(len(s_v))))
                        poly_edge_out.append([list(map(lambda n:v_index[n],pe)) for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])
                    
            if self.mode=='DIST':
                if 'Base Point' in self.inputs and self.inputs['Base Point'].links:
                    base_points = SvGetSocketAnyType(self,self.inputs['Base Point'])
                    bp_iter = repeat_last(base_points[0])
                else:
                    bp = [(0,0,0)]
                    bp_iter = repeat_last(bp)

                for v,p,v_base in zip(verts,poly_edge,bp_iter):
                    s_v = sorted( [(v_c,i) for i,v_c in enumerate(v)],key=lambda v:distK(v[0],v_base))
                    verts_out.append([vert[0] for vert in s_v])
                    if polyOutput:
                        v_index = dict(zip((i[-1] for i in s_v),range(len(s_v))))
                        poly_edge_out.append([list(map(lambda n:v_index[n],pe)) for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])

            if self.mode == 'AXIS':
                pass

            if self.mode == 'USER':
                if 'Index Data' in self.inputs and self.inputs['Index Data'].links:
                    index = SvGetSocketAnyType(self,self.inputs['Index Data'])
                else:
                    return
                    
                for v,p,i in zip(verts,poly_edge,index):
                    s_v = sorted( [(data[0],data[1],i) for i,data in enumerate(zip(i,v))],key=itemgetter(0))
                    verts_out.append([obj[1] for obj in s_v])
                    if polyOutput:
                        v_index = dict(zip((i[-1] for i in s_v),range(len(s_v))))
                        poly_edge_out.append([list(map(lambda n:v_index[n],pe)) for pe in p])
                    if orderOutput:
                        item_order.append([i[-1] for i in s_v])

            if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
                SvSetSocketAnyType(self, 'Vertices',verts_out)
            if 'PolyEdge' in self.outputs and self.outputs['PolyEdge'].links:
                SvSetSocketAnyType(self, 'PolyEdge',poly_edge_out)
            if 'Item Order' in self.outputs and self.outputs['Item Order'].links:
                SvSetSocketAnyType(self, 'Item order',item_order)

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SvVertSortNode)

def unregister():
    bpy.utils.unregister_class(SvVertSortNode)

if __name__ == "__main__":
    register()







