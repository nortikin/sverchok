import bpy
from node_s import *
from util import *
from math import sin, cos

class SphereNode(Node, SverchCustomTreeNode):
    ''' Sphere '''
    bl_idname = 'SphereNode'
    bl_label = 'Sphere'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    rad_ = bpy.props.FloatProperty(name = 'rad_', description='Radius', default=2, options={'ANIMATABLE'}, update=updateNode)
    U_ = bpy.props.IntProperty(name = 'U_', description='U', default=32, min=3, options={'ANIMATABLE'}, update=updateNode)
    V_ = bpy.props.IntProperty(name = 'V_', description='V', default=32, min=3, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Radius", "Radius")
        self.inputs.new('StringsSocket', "U", "U")
        self.inputs.new('StringsSocket', "V", "V")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "rad_", text="Radius")
        layout.prop(self, "U_", text="U")
        layout.prop(self, "V_", text="V")

    def update(self):
        # inputs
        if 'Radius' in self.inputs and self.inputs['Radius'].links:

            Radius = float(SvGetSocketAnyType(self,self.inputs['Radius'])[0][0])
        else:
            Radius = self.rad_

        if 'U' in self.inputs and self.inputs['U'].links:

            U = int(SvGetSocketAnyType(self,self.inputs['U'])[0][0])

            if U < 3:
                U = 3
        else:
            U = self.U_

        if 'V' in self.inputs and self.inputs['V'].links:
            V = int(SvGetSocketAnyType(self,self.inputs['V'])[0][0])
            if V < 3:
                V = 3
        else:
            V = self.V_

        
        nr_pts = U*V-(U-1)*2
        
        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:

            tetha = 360/U
            phi = 180/(V-1)
            listVertX = []
            listVertY = []
            listVertZ = []
            
            # this code generates more vertices than necessary. should be looked into
            for i in range(V):
                for j in range(U):
                    listVertX.append(round(Radius*cos(radians(tetha*j))*sin(radians(phi*i)),8))
                    listVertY.append(round(Radius*sin(radians(tetha*j))*sin(radians(phi*i)),8))
                    listVertZ.append(round(Radius*cos(radians(phi*i)),8))    
                X = listVertX
                Y = listVertY
                Z = listVertZ

            max_num = max(len(X), len(Y), len(Z))
            
            fullList(X,max_num)
            fullList(Y,max_num)
            fullList(Z,max_num)

            points = list(zip(X,Y,Z))
            SvSetSocketAnyType(self,'Vertices',[points[(U-1):-(U-1)]])


        if 'Edges' in self.outputs and self.outputs['Edges'].links:

            listEdg = []
            for i in range(V-2):
                for j in range(U-1):
                    listEdg.append((j+1+U*i, j+2+U*i))
                listEdg.append((U*(i+1), U*(i+1)-U+1))
            for i in range(U*(V-3)):
                listEdg.append((i+1, i+1+U))
            for i in range(U):
                listEdg.append((0, i+1))
                listEdg.append((nr_pts-1, i+nr_pts-U-1))
                
            listEdg.reverse()
            edg = [listEdg]
            SvSetSocketAnyType(self, 'Edges',[edg])

        if 'Polygons' in self.outputs and self.outputs['Polygons'].links: 

            listPln = []
            for i in range(V-3):
                listPln.append((U*i+2*U, 1+U*i+U, 1+U*i,  U*i+U))
                for j in range(U-1):
                    listPln.append((1+U*i+j+U, 2+U*i+j+U, 2+U*i+j, 1+U*i+j))

            for i in range(U-1):
                listPln.append((1+i, 2+i, 0))
                listPln.append((i+nr_pts-U, i+nr_pts-1-U, nr_pts-1))
            listPln.append((U, 1, 0))
            listPln.append((nr_pts-1-U, nr_pts-2, nr_pts-1))
            
            SvSetSocketAnyType(self,'Polygons',[listPln])



    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SphereNode)
    
def unregister():
    bpy.utils.unregister_class(SphereNode)

if __name__ == "__main__":
    register()
