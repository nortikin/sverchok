import bpy
from node_s import *
from util import *
from bpy.props import FloatVectorProperty

class SvMatrixValueIn(Node, SverchCustomTreeNode):
    ''' MatrixValueIn '''
    bl_idname = 'SvMatrixValueIn'
    bl_label = 'Matrix value input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    id_matrix = ( 1.0, 0.0, 0.0, 0.0,
                  0.0, 1.0, 0.0, 0.0,
                  0.0, 0.0, 1.0, 0.0,
                  0.0, 0.0, 0.0, 1.0) 
    
    matrix = FloatVectorProperty(name="matrix", description="matrix", 
                                            default = id_matrix, subtype='MATRIX',
                                            size=16, precision=3, update=updateNode)
    
    def init(self, context):
        self.outputs.new('MatrixSocket', "Matrix", "Matrix")
        self.width=300
        
    def draw_buttons(self, context, layout):
        col=layout.column(align=True)    
        for i in range(4):
            row = col.row(align=True)
            for j in range(i,16,4):
                row.prop(self,'matrix',text='',index=j)    
            
    def draw_buttons_ext(self, context, layout):
        pass
    
    def update(self):
         if 'Matrix' in self.outputs and self.outputs['Matrix'].links: 
            m_out = Matrix_listing([self.matrix])
            SvSetSocketAnyType(self,'Matrix',m_out)
                
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvMatrixValueIn)
    
def unregister():
    bpy.utils.unregister_class(SvMatrixValueIn)

if __name__ == "__main__":
    register()
