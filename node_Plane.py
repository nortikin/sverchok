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
        if 'Nº Vertices X' in self.inputs and self.inputs['Nº Vertices X'].is_linked:
            IntegerX = int(SvGetSocketAnyType(self,self.inputs['Nº Vertices X'])[0][0])
        else:
            IntegerX = self.int_X

        if 'Nº Vertices Y' in self.inputs and self.inputs['Nº Vertices Y'].is_linked:
            IntegerY = int(SvGetSocketAnyType(self,self.inputs['Nº Vertices Y'])[0][0])
        else:
            IntegerY = self.int_Y

        if 'Step X' in self.inputs and self.inputs['Step X'].is_linked:     
            StepX = SvGetSocketAnyType(self,self.inputs['Step X'])[0]

            listVertX = []
            fullList(StepX, IntegerX)
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

        if 'Step Y' in self.inputs and self.inputs['Step Y'].is_linked:
            StepY = SvGetSocketAnyType(self,self.inputs['Step Y'])[0]

            listVertY = []
            fullList(StepY, IntegerY)
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

        # outputs
        if 'Vertices' in self.outputs and self.outputs['Vertices'].is_linked:

            X = listVertX
            Y = listVertY
            Z = [0.0]

            max_num = max(len(X), len(Y), len(Z))
            
            fullList(X,max_num)
            fullList(Y,max_num)
            fullList(Z,max_num)

            points = list(zip(X,Y,Z))
            SvSetSocketAnyType(self, 'Vertices',[points])

        if 'Edges' in self.outputs and self.outputs['Edges'].is_linked:
            listEdg = []
            for i in range(IntegerY):
                for j in range(IntegerX-1):
                    listEdg.append((IntegerX*i+j, IntegerX*i+j+1))
            for i in range(IntegerX):
                for j in range(IntegerY-1):
                    listEdg.append((IntegerX*j+i, IntegerX*j+i+IntegerX))

            edg = list(listEdg)
            SvSetSocketAnyType(self, 'Edges',[edg])
            
        if 'Polygons' in self.outputs and self.outputs['Polygons'].is_linked:       
            listPlg = []
            for i in range(IntegerX-1):
                for j in range(IntegerY-1):
                    listPlg.append((IntegerX*j+i, IntegerX*j+i+1, IntegerX*j+i+IntegerX+1, IntegerX*j+i+IntegerX))
            plg = list(listPlg)
            SvSetSocketAnyType(self, 'Polygons',[plg])

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(PlaneNode)
    
def unregister():
    bpy.utils.unregister_class(PlaneNode)

if __name__ == "__main__":
    register()
