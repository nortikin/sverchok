import bpy
from node_s import *
from mathutils import *
from util import *

class MatrixShearNode(Node, SverchCustomTreeNode):
    ''' Construct a Shear Matirx '''
    bl_idname = 'MatrixShearNode'
    bl_label = 'Shear Matrix'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    # select Shear plane
    
    mode_items = [
           ("XY",       "XY-plane",        ""),
           ("XZ",       "XZ-plane",        ""),     
           ("YZ",       "YZ-plane",        ""),  
    ]   
    factor1_ = bpy.props.FloatProperty(name = 'factor1_', description='Factor1', default=0.0, options={'ANIMATABLE'}, update=updateNode)
    factor2_ = bpy.props.FloatProperty(name = 'factor2_', description='Factor2', default=0.0, options={'ANIMATABLE'}, update=updateNode)
     
    plane_=bpy.props.EnumProperty( items = mode_items, name="Plane", 
            description="Function choice", default="XY", update=updateNode)
            
            
    def init(self, context):
        self.inputs.new('StringsSocket', "Factor1", "Factor2")
        self.inputs.new('StringsSocket', "Factor2", "Factor2")
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")
        
    def draw_buttons(self, context, layout):
        layout.prop(self,"plane_","Shear plane:");

        layout.prop(self, "factor1_", text="Factor 1")
        layout.prop(self, "factor2_", text="Factor 2")

    def update(self):
        # inputs
        factor1 = []
        factor2 = []
        if 'Factor1' in self.inputs and self.inputs['Factor1'].links and \
            type(self.inputs['Factor1'].links[0].from_socket) == StringsSocket:
            if not self.inputs['Factor1'].node.socket_value_update:
                self.inputs['Factor1'].node.update()
            factor1 = eval(self.inputs['Factor1'].links[0].from_socket.StringsProperty)
        if not factor1:
            factor1 = [[self.factor1_]]
        
        if 'Factor2' in self.inputs and self.inputs['Factor2'].links and \
            type(self.inputs['Factor2'].links[0].from_socket) == StringsSocket:
            if not self.inputs['Factor2'].node.socket_value_update:
                self.inputs['Factor2'].node.update()
            factor2 = eval(self.inputs['Factor2'].links[0].from_socket.StringsProperty)
        if not factor2:
            factor2 = [[self.factor2_]]
        
        
        # outputs
    
        if 'Matrix' in self.outputs and self.outputs['Matrix'].links: 
            if not self.outputs['Matrix'].node.socket_value_update:
                self.outputs['Matrix'].node.update()
    
            max_l = max(len(factor1),len(factor2))
            fullList(factor1,max_l)
            fullList(factor2,max_l)
            matrixes_=[]
            for i in range(max_l):
                max_inner = max(len(factor1[i]),len(factor2[i]))
                fullList(factor1[i],max_inner)
                fullList(factor2[i],max_inner)
                for j in range(max_inner):
                    matrixes_.append(Matrix.Shear(self.plane_,4,(factor1[i][j],factor2[i][j])))
            
            matrixes = Matrix_listing(matrixes_)
            self.outputs['Matrix'].MatrixProperty = str(matrixes)
        
                
    def update_socket(self, context):
        self.update()


    

def register():
    bpy.utils.register_class(MatrixShearNode)
    
def unregister():
    bpy.utils.unregister_class(MatrixShearNode)

if __name__ == "__main__":
    register()