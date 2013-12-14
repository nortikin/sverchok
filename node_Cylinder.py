import bpy
from node_s import *
from util import *
from math import sin, cos

class CylinderNode(Node, SverchCustomTreeNode):
    ''' Cylinder '''
    bl_idname = 'CylinderNode'
    bl_label = 'Cylinder'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    radTop_ = bpy.props.FloatProperty(name = 'radTop_', description='Radius Top', default=2.0, options={'ANIMATABLE'}, update=updateNode)
    radBot_ = bpy.props.FloatProperty(name = 'radBot_', description='Radius Bottom', default=2.0, options={'ANIMATABLE'}, update=updateNode)
    vert_ = bpy.props.IntProperty(name = 'vert_', description='Vertices', default=32, min=3, options={'ANIMATABLE'}, update=updateNode)
    height_ = bpy.props.FloatProperty(name = 'height_', description='Height', default=5.0, options={'ANIMATABLE'}, update=updateNode)
    subd_ = bpy.props.IntProperty(name = 'subd_', description='Subdivisions', default=0, min=0,options={'ANIMATABLE'}, update=updateNode)
    cap_ = bpy.props.BoolProperty(name = 'cap_', description='Caps', default=0, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "RadTop", "RadTop")
        self.inputs.new('StringsSocket', "RadBot", "RadBot")
        self.inputs.new('StringsSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Height", "Height")
        self.inputs.new('StringsSocket', "Subdivisions", "Subdivisions")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "radTop_", text="Radius Top")
        layout.prop(self, "radBot_", text="Radius Bottom")
        layout.prop(self, "vert_", text="Nº Vert")
        layout.prop(self, "height_", text="Height")
        layout.prop(self, "subd_", text="Subdivisions")
        layout.prop(self, "cap_", text="Caps")

    def update(self):
        # inputs
        if len(self.inputs['RadTop'].links)>0:
            if not self.inputs['RadTop'].node.socket_value_update:
                self.inputs['RadTop'].node.update()
            RadiusTop = float(eval(self.inputs['RadTop'].links[0].from_socket.StringsProperty)[0][0])
        else:
            RadiusTop = self.radTop_

        if len(self.inputs['RadBot'].links)>0:
            if not self.inputs['RadBot'].node.socket_value_update:
                self.inputs['RadBot'].node.update()
            RadiusBot = float(eval(self.inputs['RadBot'].links[0].from_socket.StringsProperty)[0][0])
        else:
            RadiusBot = self.radBot_

        if len(self.inputs['Vertices'].links)>0:
            if not self.inputs['Vertices'].node.socket_value_update:
                self.inputs['Vertices'].node.update()
            Vertices = int(eval(self.inputs['Vertices'].links[0].from_socket.StringsProperty)[0][0])
            if Vertices < 3:
                Vertices = 3
        else:
            Vertices = self.vert_

        if len(self.inputs['Height'].links)>0:
            if not self.inputs['Height'].node.socket_value_update:
                self.inputs['Height'].node.update()
            Height = float(eval(self.inputs['Height'].links[0].from_socket.StringsProperty)[0][0])
        else:
            Height = self.height_

        if len(self.inputs['Subdivisions'].links)>0:
            if not self.inputs['Subdivisions'].node.socket_value_update:
                self.inputs['Subdivisions'].node.update()
            Subd = int(eval(self.inputs['Subdivisions'].links[0].from_socket.StringsProperty)[0][0])
            if Subd < 0:
                Subd = 0
        else:
            Subd = self.subd_


        tetha = 360/Vertices
        heightSubd = Height/(Subd+1)
        listVertX = []
        listVertY = []
        listVertZ = []

        for i in range(Subd+2):
            radius = RadiusBot - ((RadiusBot-RadiusTop)/(Subd+1))*i
            for j in range(Vertices):
                listVertX.append(radius*cos(radians(tetha*j)))
                listVertY.append(radius*sin(radians(tetha*j)))
                listVertZ.append(heightSubd*i)

        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.inputs['Nº Vertices'].node.update()

            X = listVertX
            Y = listVertY
            Z = listVertZ

            max_num = max(len(X), len(Y), len(Z))
            
            self.fullList(X,max_num)
            self.fullList(Y,max_num)
            self.fullList(Z,max_num)

            points = list(zip(X,Y,Z))
            self.outputs['Vertices'].VerticesProperty = str([points])

        if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
            if not self.outputs['Edges'].node.socket_value_update:
                self.inputs['Edges'].node.update()

            listEdg = []
            for i in range(Subd+2):
                for j in range(Vertices-1):
                    listEdg.append((j+Vertices*i, j+1+Vertices*i))
                listEdg.append((Vertices-1+Vertices*i, 0+Vertices*i))

            for i in range(Subd+1):
                for j in range(Vertices):
                    listEdg.append((j+Vertices*i, j+Vertices+Vertices*i))

            edg = list(listEdg)
            self.outputs['Edges'].StringsProperty = str([edg])

        if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
            if not self.outputs['Polygons'].node.socket_value_update:
                self.inputs['Polygons'].node.update()

            listPlg = []
            for i in range(Subd+1):
                for j in range(Vertices-1):
                    listPlg.append((j+Vertices*i, j+1+Vertices*i, j+1+Vertices*i+Vertices, j+Vertices*i+Vertices))
                listPlg.append((Vertices-1+Vertices*i, 0+Vertices*i, 0+Vertices*i+Vertices, Vertices-1+Vertices*i+Vertices))

            if self.cap_ == 1:
                capBot = []
                capTop = []
                for i in range(Vertices):
                    capBot.append(i)
                    capTop.append(Vertices*(Subd+1)+i)
                capBot.reverse()
                listPlg.append(capBot)
                listPlg.append(capTop)

            plg = [listPlg]
            self.outputs['Polygons'].StringsProperty = str(plg)

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(CylinderNode)
    
def unregister():
    bpy.utils.unregister_class(CylinderNode)

if __name__ == "__main__":
    register()
