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
        if len(self.inputs['Radius'].links)>0:
            if not self.inputs['Radius'].node.socket_value_update:
                self.inputs['Radius'].node.update()
            Radius = float(eval(self.inputs['Radius'].links[0].from_socket.StringsProperty)[0][0])
        else:
            Radius = self.rad_

        if len(self.inputs['U'].links)>0:
            if not self.inputs['U'].node.socket_value_update:
                self.inputs['U'].node.update()
            U = int(eval(self.inputs['U'].links[0].from_socket.StringsProperty)[0][0])
            if U < 3:
                U = 3

        else:
            U = self.U_

        if len(self.inputs['V'].links)>0:
            if not self.inputs['V'].node.socket_value_update:
                self.inputs['V'].node.update()
            V = int(eval(self.inputs['V'].links[0].from_socket.StringsProperty)[0][0])
            if V < 3:
                V = 3

        else:
            V = self.V_

        tetha = 360/U
        phi = 180/(V-1)
        listVertX = []
        listVertY = []
        listVertZ = []
        for i in range(V):
            for j in range(U):
                listVertX.append(round(Radius*cos(radians(tetha*j))*sin(radians(phi*i)),2))
                listVertY.append(round(Radius*sin(radians(tetha*j))*sin(radians(phi*i)),2))
                listVertZ.append(round(Radius*cos(radians(phi*i)),2))

        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.outputs['Vertices'].node.update()

            X = listVertX
            Y = listVertY
            Z = listVertZ

            max_num = max(len(X), len(Y), len(Z))
            
            self.fullList(X,max_num)
            self.fullList(Y,max_num)
            self.fullList(Z,max_num)

            points = list(zip(X,Y,Z))
            for i in range(U-1):
                points.pop(0)
                l = len(points)
                points.pop(l-1)
            self.outputs['Vertices'].VerticesProperty = str([points])

        if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
            if not self.outputs['Edges'].node.socket_value_update:
                self.inputs['Edges'].node.update()

            listEdg = []
            for i in range(V-2):
                for j in range(U-1):
                    listEdg.append((j+1+U*i, j+2+U*i))
                listEdg.append((U*(i+1), U*(i+1)-U+1))
            for i in range(U*(V-3)):
                listEdg.append((i+1, i+1+U))
            for i in range(U):
                listEdg.append((0, i+1))
                listEdg.append((len(points)-1, i+len(points)-U-1))
                
            listEdg.reverse()
            edg = [listEdg]
            self.outputs['Edges'].StringsProperty = str(edg)

        if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
            if not self.outputs['Polygons'].node.socket_value_update:
                self.inputs['Polygons'].node.update()

            listPln = []
            for i in range(V-3):
                listPln.append((U*i+2*U, 1+U*i+U, 1+U*i,  U*i+U))
                for j in range(U-1):
                    listPln.append((1+U*i+j+U, 2+U*i+j+U, 2+U*i+j, 1+U*i+j))

            for i in range(U-1):
                listPln.append((1+i, 2+i, 0))
                listPln.append((i+len(points)-U, i+len(points)-1-U, len(points)-1))
            listPln.append((U, 1, 0))
            listPln.append((len(points)-1-U, len(points)-2, len(points)-1))
            
            
            pln = [listPln]
            self.outputs['Polygons'].StringsProperty = str(pln)

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SphereNode)
    
def unregister():
    bpy.utils.unregister_class(SphereNode)

if __name__ == "__main__":
    register()
