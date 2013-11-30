import bpy
from node_s import *
from util import *

class ImageNode(Node, SverchCustomTreeNode):
    ''' Image '''
    bl_idname = 'ImageNode'
    bl_label = 'Image'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Xvecs = bpy.props.IntProperty(name='Xvecs', description='Xvecs', default=10, min=2, max=1000, options={'ANIMATABLE'}, update=updateNode)
    Yvecs = bpy.props.IntProperty(name='Yvecs', description='Yvecs', default=10, min=2, max=1000, options={'ANIMATABLE'}, update=updateNode)
    name_image = bpy.props.StringProperty(name='image_name', description='image name', default='', update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "vecs X", "vecs X")
        self.inputs.new('StringsSocket', "vecs Y", "vecs Y")
        self.inputs.new('StringsSocket', "Step X", "Step X")
        self.inputs.new('StringsSocket', "Step Y", "Step Y")
        self.outputs.new('VerticesSocket', "vecs", "vecs")
        self.outputs.new('StringsSocket', "edgs", "edgs")
        self.outputs.new('StringsSocket', "pols", "pols")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Xvecs", text="vectors X №")
        layout.prop(self, "Yvecs", text="vectors Y №")
        layout.prop(self, "name_image", text="image_name")

    def update(self):
        # inputs
        if len(self.inputs['vecs X'].links)>0:
            if not self.inputs['vecs X'].node.socket_value_update:
                self.inputs['vecs X'].node.update()
            IntegerX = int(eval(self.inputs['vecs X'].links[0].from_socket.StringsProperty)[0][0])
        else:
            IntegerX = self.Xvecs

        if len(self.inputs['vecs Y'].links)>0:
            if not self.inputs['vecs Y'].node.socket_value_update:
                self.inputs['vecs Y'].node.update()
            IntegerY = int(eval(self.inputs['vecs Y'].links[0].from_socket.StringsProperty)[0][0])
        else:
            IntegerY = self.Yvecs

        if len(self.inputs['Step X'].links)>0:
            if not self.inputs['Step X'].node.socket_value_update:
                self.inputs['Step X'].node.update()
            StepX = eval(self.inputs['Step X'].links[0].from_socket.StringsProperty)[0]

            listVertX = []
            self.fullList(StepX, IntegerX)
            for i in range(IntegerY):
                listVertX.append(0.0)
                for j in range(IntegerX-1):
                    listVertX.append(round(listVertX[j]+StepX[j], 2))
        else:
            StepX = [[1]]
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
            StepY = [[1]]
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
    
    def make_vertices(self, delitelx, delitely, stepx, stepy, image_name):
        lenx = bpy.data.images[image_name].size[0]
        leny = bpy.data.images[image_name].size[1]
        
        xcoef = lenx/delitelx
        ycoef = leny/delitely
        
        pixy = []
        for y_ in range(delitely):
            pixx = []
            y = y_*ycoef
            for x_ in range(delitelx):
                x = int(4*x_*xcoef+y)
                middle = sum(bpy.data.images[image_name].pixels[x:x+4])/4
                pixx.append(middle)
            pixy.append(pixx)
        len_ver_x = len(pixy[0])
        len_ver_y = len(pixy)
        print (len_ver_x, len_ver_y)
        overall_length = len_ver_x*len_ver_y
        vertices = []
        y = 0
        for i, y in enumerate(range(len_ver_y)):
            for k, x in enumerate(range(len_ver_y)):
                
                vertex = (x,y,pixy[y][x])
                vertices.append(vertex)
        return vertices
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ImageNode)
    
def unregister():
    bpy.utils.unregister_class(ImageNode)

if __name__ == "__main__":
    register()
