import bpy
from mathutils import Vector, Matrix
from node_s import *
from util import *

class DistancePPNode(Node, SverchCustomTreeNode):
    ''' Distance Point to Point '''
    bl_idname = 'DistancePPNode'
    bl_label = 'Distances'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Cross_dist = bpy.props.BoolProperty(name='Cross_dist', description='DANGEROUSE! If crossover dimension calculation, be sure', default=False)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices1', 'vertices1')
        self.inputs.new('MatrixSocket', 'matrix1', 'matrix1')
        self.inputs.new('VerticesSocket', 'vertices2', 'vertices2')
        self.inputs.new('MatrixSocket', 'matrix2', 'matrix2')
        self.outputs.new('StringsSocket', 'distances', 'distances')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Cross_dist", text="CrossOver")
        
    def update(self):
        for name in ['vertices1', 'vertices2','matrix1','matrix2']:
            if not name in self.inputs:
                return
                
        if self.inputs['vertices1'].links and self.inputs['vertices2'].links:
            prop1_ = SvGetSocketAnyType(self,self.inputs['vertices1'])
            prop1 = Vector_generate(prop1_)
            prop2_ = SvGetSocketAnyType(self,self.inputs['vertices2'])
            prop2 = Vector_generate(prop2_)
                
        elif self.inputs['matrix1'].links and self.inputs['matrix2'].links:        
            propa = SvGetSocketAnyType(self,self.inputs['matrix1'])
            prop1 = Matrix_location(Matrix_generate(propa))
            propb = SvGetSocketAnyType(self,self.inputs['matrix2'])
            prop2 = Matrix_location(Matrix_generate(propb))
        else:
            prop1, prop2 = [], []

        if prop1 and prop2:
            if self.outputs['distances'].links:
                #print ('distances input', str(prop1), str(prop2))
                if self.Cross_dist:
                    output = self.calcM(prop1, prop2)
                else:
                    output = self.calcV(prop1, prop2)
                SvSetSocketAnyType(self,'distances',output)
                
                #print ('distances out' , str(output))
        else:
            SvSetSocketAnyType(self,'distances', [])
    
    def calcV(self, list1, list2):
        dists = []
        lenlis = min(len(list1),len(list2)) -1
        for i, object1 in enumerate(list1):
            if i > lenlis:
                continue
            values = []
            lenlen = min(len(object1),len(list2[i])) -1
            for k, vert1 in enumerate(object1):
                if k > lenlen:
                    continue
                values.append(self.distance(vert1, list2[i][k]))
            dists.append(values)
        #print(dists)
        return dists
    
    def calcM(self, list1, list2):
        ll1, ll2 = len(list1[0]), len(list2[0])
        if ll1 > ll2:
            short = list2
            long = list1        
        else:
            short = list1
            long = list2
        dists = []
        for obsh in short:
            obshdis = []
            for vers in obsh:
                for obln in long:
                    oblndis = []
                    for verl in obln:
                        oblndis.append(self.distance(vers,verl))
                    obshdis.append(oblndis)
            dists.append(obshdis)
        #print(dists)
        return dists[0]
    
    def distance(self, x, y):
        vec = Vector((x[0]-y[0], x[1]-y[1], x[2]-y[2]))
        return vec.length
    
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(DistancePPNode)
    
def unregister():
    bpy.utils.unregister_class(DistancePPNode)

if __name__ == "__main__":
    register()
