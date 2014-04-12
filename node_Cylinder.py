import bpy
from node_s import *
from util import *
from math import sin, cos

class CylinderNode(Node, SverchCustomTreeNode):
    ''' Cylinder '''
    bl_idname = 'CylinderNode'
    bl_label = 'Cylinder'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    radTop_ = bpy.props.FloatProperty(name = 'radTop_', description='Radius Top', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    radBot_ = bpy.props.FloatProperty(name = 'radBot_', description='Radius Bottom', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    vert_ = bpy.props.IntProperty(name = 'vert_', description='Vertices', default=32, min=3, options={'ANIMATABLE'}, update=updateNode)
    height_ = bpy.props.FloatProperty(name = 'height_', description='Height', default=2.0, options={'ANIMATABLE'}, update=updateNode)
    subd_ = bpy.props.IntProperty(name = 'subd_', description='Subdivisions', default=0, min=0,options={'ANIMATABLE'}, update=updateNode)
    cap_ = bpy.props.BoolProperty(name = 'cap_', description='Caps', default=True, options={'ANIMATABLE'}, update=updateNode)
    Separate = bpy.props.BoolProperty(name = 'Separate', description='Separate UV coords', default=True, update=updateNode)

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
        row = layout.row(align=True)
        row.prop(self, "Separate", text="Separate")
        row.prop(self, "cap_", text="Caps")
        layout.prop(self, "radTop_", text="Radius Top")
        layout.prop(self, "radBot_", text="Radius Bottom")
        layout.prop(self, "vert_", text="Nº Vert")
        layout.prop(self, "height_", text="Height")
        layout.prop(self, "subd_", text="Subdivisions")

    def update(self):
        # inputs
        if 'RadTop' in self.inputs and self.inputs['RadTop'].links:
            RadiusTop = float(SvGetSocketAnyType(self,self.inputs['RadTop'])[0][0])
        else:
            RadiusTop = self.radTop_

        if 'RadBot' in self.inputs and self.inputs['RadBot'].links:
            RadiusBot = float(SvGetSocketAnyType(self,self.inputs['RadBot'])[0][0])
        else:
            RadiusBot = self.radBot_

        if 'Vertices' in self.inputs and self.inputs['Vertices'].links:
            Vertices = int(SvGetSocketAnyType(self,self.inputs['Vertices'])[0][0])
            if Vertices < 3:
                Vertices = 3
        else:
            Vertices = self.vert_

        if 'Height' in self.inputs and self.inputs['Height'].links:
            Height = float(SvGetSocketAnyType(self,self.inputs['Height'])[0][0])
        else:
            Height = self.height_

        if 'Subdivisions' in self.inputs and self.inputs['Subdivisions'].links:
            Subd = int(SvGetSocketAnyType(self,self.inputs['Subdivisions'])[0][0])
            if Subd < 0:
                Subd = 0
        else:
            Subd = self.subd_

        theta = 360/Vertices
        heightSubd = Height/(Subd+1)
        listVertX = []
        listVertY = []
        listVertZ = []

        for i in range(Subd+2):
            radius = RadiusBot - ((RadiusBot-RadiusTop)/(Subd+1))*i
            for j in range(Vertices):
                listVertX.append(radius*cos(radians(theta*j)))
                listVertY.append(radius*sin(radians(theta*j)))
                listVertZ.append(heightSubd*i)

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:

            X = listVertX
            Y = listVertY
            Z = listVertZ

            max_num = max(len(X), len(Y), len(Z))
            
            fullList(X,max_num)
            fullList(Y,max_num)
            fullList(Z,max_num)

            points = list(sv_zip(X,Y,Z))
            if self.Separate:
                out=[]
                for y in range(Vertices):
                    out_=[]
                    for x in range(Subd+2):
                        out_.append(points[Subd+2*y+x])
                    out.append(out_)
                SvSetSocketAnyType(self, 'Vertices',[out])
            else:
                SvSetSocketAnyType(self, 'Vertices',[points])
                

        if 'Edges' in self.outputs and self.outputs['Edges'].links:

            listEdg = []
            for i in range(Subd+2):
                for j in range(Vertices-1):
                    listEdg.append([j+Vertices*i, j+1+Vertices*i])
                listEdg.append([Vertices-1+Vertices*i, 0+Vertices*i])

            for i in range(Subd+1):
                for j in range(Vertices):
                    listEdg.append([j+Vertices*i, j+Vertices+Vertices*i])

            edg = list(listEdg)
            SvSetSocketAnyType(self, 'Edges',[edg])

        if 'Polygons' in self.outputs and self.outputs['Polygons'].links:

            listPlg = []
            for i in range(Subd+1):
                for j in range(Vertices-1):
                    listPlg.append([j+Vertices*i, j+1+Vertices*i, j+1+Vertices*i+Vertices, j+Vertices*i+Vertices])
                listPlg.append([Vertices-1+Vertices*i, 0+Vertices*i, 0+Vertices*i+Vertices, Vertices-1+Vertices*i+Vertices])

            if self.cap_ == 1:
                capBot = []
                capTop = []
                for i in range(Vertices):
                    capBot.append(i)
                    capTop.append(Vertices*(Subd+1)+i)
                capBot.reverse()
                listPlg.append(capBot)
                listPlg.append(capTop)

            
            SvSetSocketAnyType(self, 'Polygons',[listPlg])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(CylinderNode)
    
def unregister():
    bpy.utils.unregister_class(CylinderNode)

if __name__ == "__main__":
    register()
