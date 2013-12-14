import bpy
from node_s import *
from util import *
from math import sin, cos

class CircleNode(Node, SverchCustomTreeNode):
    ''' Circle '''
    bl_idname = 'CircleNode'
    bl_label = 'Circle'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    rad_ = bpy.props.FloatProperty(name = 'rad_', description='Radius', default=2, options={'ANIMATABLE'}, update=updateNode)
    vert_ = bpy.props.IntProperty(name = 'vert_', description='Vertices', default=32, min=3, options={'ANIMATABLE'}, update=updateNode)
    degr_ = bpy.props.FloatProperty(name = 'degr_', description='Degrees', default=360, min=0, max=360, options={'ANIMATABLE'}, update=updateNode)
    mode_ = bpy.props.BoolProperty(name = 'mode_', description='Mode', default=0, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Radius", "Radius")
        self.inputs.new('StringsSocket', "Nº Vertices", "Nº Vertices")
        self.inputs.new('StringsSocket', "Degrees", "Degrees")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "rad_", text="Radius")
        layout.prop(self, "vert_", text="Nº Vert")
        layout.prop(self, "degr_", text="Degrees")
        layout.prop(self, "mode_", text="Mode")

    def update(self):
        # inputs
        if len(self.inputs['Radius'].links)>0:
            if not self.inputs['Radius'].node.socket_value_update:
                self.inputs['Radius'].node.update()
            Radius = float(eval(self.inputs['Radius'].links[0].from_socket.StringsProperty)[0][0])
        else:
            Radius = self.rad_

        if len(self.inputs['Nº Vertices'].links)>0:
            if not self.inputs['Nº Vertices'].node.socket_value_update:
                self.inputs['Nº Vertices'].node.update()
            Vertices = int(eval(self.inputs['Nº Vertices'].links[0].from_socket.StringsProperty)[0][0])
            if Vertices < 3:
                Vertices = 3
        else:
            Vertices = self.vert_

        if len(self.inputs['Degrees'].links)>0:
            if not self.inputs['Degrees'].node.socket_value_update:
                self.inputs['Degrees'].node.update()
            Angle = int(eval(self.inputs['Degrees'].links[0].from_socket.StringsProperty)[0][0])
            if Angle < 0:
                Angle = 0
            elif Angle > 360:
                Angle = 360
        else:
            Angle = self.degr_

        if Angle < 360:
            tetha = Angle/(Vertices-1)
        else:
            tetha = Angle/Vertices
        listVertX = []
        listVertY = []
        for i in range(Vertices):
            listVertX.append(Radius*cos(radians(tetha*i)))
            listVertY.append(Radius*sin(radians(tetha*i)))

        if Angle < 360 and self.mode_ == 0:
            listVertX.pop()
            listVertY.pop()
            listVertX.insert(Vertices, (Radius*cos(radians(Angle))))
            listVertY.insert(Vertices, (Radius*sin(radians(Angle))))
        elif Angle < 360 and self.mode_ == 1:
            listVertX.append(0.0)
            listVertY.append(0.0)
        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.inputs['Nº Vertices'].node.update()

            X = listVertX
            Y = listVertY
            Z = [0.0]

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
            for i in range(Vertices-1):
                listEdg.append((i, i+1))
            if Angle < 360 and self.mode_ == 1:
                listEdg.append((0, Vertices))
                listEdg.append((Vertices-1, Vertices))
            else:
                listEdg.append((0, Vertices-1))
            edg = list(listEdg)
            self.outputs['Edges'].StringsProperty = str([edg])

        if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
            if not self.outputs['Polygons'].node.socket_value_update:
                self.inputs['Polygons'].node.update()

            listPlg = []
            for i in range(Vertices):
                listPlg.append(i)
            if Angle < 360 and self.mode_ == 1:
                listPlg.insert(0, Vertices)

            plg = [listPlg]
            self.outputs['Polygons'].StringsProperty = str([plg])

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(CircleNode)
    
def unregister():
    bpy.utils.unregister_class(CircleNode)

if __name__ == "__main__":
    register()
