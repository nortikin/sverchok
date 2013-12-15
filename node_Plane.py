import bpy
from node_s import *
from util import *

class PlaneNode(Node, SverchCustomTreeNode):
    ''' Plane '''
    bl_idname = 'PlaneNode'
    bl_label = 'Plane'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    int_X = bpy.props.IntProperty(name = 'int_X', description='Nº Vertices X', default=2, min=2, options={'ANIMATABLE'}, update=updateNode)
    int_Y = bpy.props.IntProperty(name = 'int_Y', description='Nº Vertices Y', default=2, min=2, options={'ANIMATABLE'}, update=updateNode)
    step_X = bpy.props.FloatProperty(name = 'step_X', description='Step length X', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    step_Y = bpy.props.FloatProperty(name = 'step_Y', description='Step length Y', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "Nº Vertices X", "Nº Vertices X")
        self.inputs.new('StringsSocket', "Nº Vertices Y", "Nº Vertices Y")
        self.inputs.new('StringsSocket', "Step X", "Step length X")
        self.inputs.new('StringsSocket', "Step Y", "Step length Y")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "int_X", text="Nº Vert X")
        layout.prop(self, "int_Y", text="Nº Vert Y")
        layout.prop(self, "step_X", text="Step X")
        layout.prop(self, "step_Y", text="Step Y")

    def update(self):
        # inputs
        if len(self.inputs['Nº Vertices X'].links)>0:
            if not self.inputs['Nº Vertices X'].node.socket_value_update:
                self.inputs['Nº Vertices X'].node.update()
            IntegerX = int(eval(self.inputs['Nº Vertices X'].links[0].from_socket.StringsProperty)[0][0])
        else:
            IntegerX = self.int_X

        if len(self.inputs['Nº Vertices Y'].links)>0:
            if not self.inputs['Nº Vertices Y'].node.socket_value_update:
                self.inputs['Nº Vertices Y'].node.update()
            IntegerY = int(eval(self.inputs['Nº Vertices Y'].links[0].from_socket.StringsProperty)[0][0])
        else:
            IntegerY = self.int_Y

        if len(self.inputs['Step X'].links)>0:
            if not self.inputs['Step X'].node.socket_value_update:
                self.inputs['Step X'].node.update()
            StepX = eval(self.inputs['Step X'].links[0].from_socket.StringsProperty)[0]

            listVertX = []
            self.fullList(StepX, IntegerX)
            for i in range(IntegerY):
                listVertX.append(0.0)
                for j in range(IntegerX-1):
                    listVertX.append(listVertX[j]+StepX[j])

        else:
            StepX = self.step_X
            listVertX = []
            for i in range(IntegerY):
                for j in range(IntegerX):
                    listVertX.append(0.0+j)
            listVertX = [StepX*i for i in listVertX]

        if len(self.inputs['Step Y'].links)>0:
            if not self.inputs['Step Y'].node.socket_value_update:
                self.inputs['Step Y'].node.update()
            StepY = eval(self.inputs['Step Y'].links[0].from_socket.StringsProperty)[0]

            listVertY = []
            self.fullList(StepY, IntegerY)
            for i in range(IntegerX):
                listVertY.append(0.0)
            for i in range(IntegerY-1):
                for j in range(IntegerX):
                    listVertY.append(round(listVertY[IntegerX*i]+StepY[i], 2))
        else:
            StepY = self.step_Y
            listVertY = []
            for i in range(IntegerY):
                for j in range(IntegerX):
                    listVertY.append(0.0+i)
            listVertY = [StepY*i for i in listVertY]

        #print('.....IntegerY.....',IntegerY, IntegerX)
        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.outputs['Nº Vertices'].node.update()

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
                self.outputs['Edges'].node.update()

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
                self.outputs['Polygons'].node.update()

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
