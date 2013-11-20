import bpy
from node_s import *
from util import *

class PlaneNode(Node, SverchCustomTreeNode):
    ''' Plane '''
    bl_idname = 'PlaneNode'
    bl_label = 'Plane'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_X = bpy.props.IntProperty(name = 'int_X', description='plane', default=2, min=2, options={'ANIMATABLE'}, update=updateNode)
    int_Y = bpy.props.IntProperty(name = 'int_Y', description='plane', default=2, min=2, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices X", "Nº Vertices X")
        self.inputs.new('StringsSocket', "Nº Vertices Y", "Nº Vertices Y")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "int_X", text="Nº Vert X")
        layout.prop(self, "int_Y", text="Nº Vert Y")


    def update(self):
        # inputs
        if len(self.inputs['Nº Vertices X'].links)>0:
            if not self.inputs['Nº Vertices X'].node.socket_value_update:
                self.inputs['Nº Vertices X'].node.update()
            IntegerX = eval(self.inputs['Nº Vertices X'].links[0].from_socket.StringsProperty)[0][0]
        else:
            IntegerX = self.int_X

        if len(self.inputs['Nº Vertices Y'].links)>0:
            if not self.inputs['Nº Vertices Y'].node.socket_value_update:
                self.inputs['Nº Vertices Y'].node.update()
            IntegerY = eval(self.inputs['Nº Vertices Y'].links[0].from_socket.StringsProperty)[0][0]
        else:
            IntegerY = self.int_Y
        
        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.inputs['Nº Vertices'].node.update()

            listVertX = []
            for i in range(IntegerY):
                for j in range(IntegerX):
                    listVertX.append(0.0+j)
            listVertY = []
            for i in range(IntegerY):
                for j in range(IntegerX):
                    listVertY.append(0.0+i)

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
            for i in range(IntegerY):
                for j in range(IntegerX-1):
                    listEdg.append((IntegerX*i+j, IntegerX*i+j+1))
            for i in range(IntegerX):
                for j in range(IntegerY-1):
                    listEdg.append((IntegerX*j+i, IntegerX*j+i+IntegerX))

            edg = list(listEdg)
            self.outputs['Edges'].StringsProperty = str([edg])

        if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
            if not self.outputs['Polygons'].node.socket_value_update:
                self.inputs['Polygons'].node.update()

            listPlg = []
            for i in range(IntegerX-1):
                for j in range(IntegerY-1):
                    listPlg.append((IntegerX*j+i, IntegerX*j+i+1, IntegerX*j+i+IntegerX+1, IntegerX*j+i+IntegerX))
            plg = list(listPlg)
            self.outputs['Polygons'].StringsProperty = str([plg])

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(PlaneNode)
    
def unregister():
    bpy.utils.unregister_class(PlaneNode)

if __name__ == "__main__":
    register()
