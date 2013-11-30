import bpy
from node_s import *
from util import *

class ImageNode(Node, SverchCustomTreeNode):
    ''' Image '''
    bl_idname = 'ImageNode'
    bl_label = 'Image'
    bl_icon = 'OUTLINER_OB_EMPTY'
    Xvecs = bpy.props.IntProperty(name='Xvecs', description='Xvecs', default=10, min=2, max=30, options={'ANIMATABLE'}, update=updateNode)
    Yvecs = bpy.props.IntProperty(name='Yvecs', description='Yvecs', default=10, min=2, max=30, options={'ANIMATABLE'}, update=updateNode)
    Xstep = bpy.props.FloatProperty(name='Xstep', description='Xstep', default=1.0, min=0.01, max=100, options={'ANIMATABLE'}, update=updateNode)
    Ystep = bpy.props.FloatProperty(name='Ystep', description='Ystep', default=1.0, min=0.01, max=100, options={'ANIMATABLE'}, update=updateNode)
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
        layout.prop(self, "Xvecs", text="vectors X")
        layout.prop(self, "Yvecs", text="vectors Y")
        layout.prop(self, "Xstep", text="step X")
        layout.prop(self, "Ystep", text="step Y")
        layout.prop(self, "name_image", text="image_name")

    def update(self):
        # inputs
        if len(self.inputs['vecs X'].links)>0:
            if not self.inputs['vecs X'].node.socket_value_update:
                self.inputs['vecs X'].node.update()
            IntegerX = int(eval(self.inputs['vecs X'].links[0].from_socket.StringsProperty)[0][0])
        else:
            IntegerX = max(int(self.Xvecs),30)

        if len(self.inputs['vecs Y'].links)>0:
            if not self.inputs['vecs Y'].node.socket_value_update:
                self.inputs['vecs Y'].node.update()
            IntegerY = int(eval(self.inputs['vecs Y'].links[0].from_socket.StringsProperty)[0][0])
        else:
            IntegerY = max(int(self.Yvecs),30)

        if len(self.inputs['Step X'].links)>0:
            if not self.inputs['Step X'].node.socket_value_update:
                self.inputs['Step X'].node.update()
            StepX = eval(self.inputs['Step X'].links[0].from_socket.StringsProperty)[0]
            self.fullList(StepX, IntegerX)
            
        else:
            StepX = [self.Xstep]
            self.fullList(StepX, IntegerX)

        if len(self.inputs['Step Y'].links)>0:
            if not self.inputs['Step Y'].node.socket_value_update:
                self.inputs['Step Y'].node.update()
            StepY = eval(self.inputs['Step Y'].links[0].from_socket.StringsProperty)[0]
            self.fullList(StepY, IntegerY)
            
        else:
            StepY = [self.Ystep]
            self.fullList(StepY, IntegerY)

        # outputs
        if 'vecs' in self.outputs and len(self.outputs['vecs'].links)>0:
            if not self.outputs['vecs'].node.socket_value_update:
                self.outputs['vecs'].node.update()
            
            out = self.make_vertices(IntegerX, IntegerY, StepX, StepY, self.name_image)
            #print 
            self.outputs['vecs'].VerticesProperty = str([out])
        else:
            self.outputs['vecs'].VerticesProperty = str([[[]]])

        if 'edgs' in self.outputs and len(self.outputs['edgs'].links)>0:
            if not self.outputs['edgs'].node.socket_value_update:
                self.inputs['edgs'].node.update()

            listEdg = []
            for i in range(IntegerY):
                for j in range(IntegerX-1):
                    listEdg.append((IntegerX*i+j, IntegerX*i+j+1))
            for i in range(IntegerX):
                for j in range(IntegerY-1):
                    listEdg.append((IntegerX*j+i, IntegerX*j+i+IntegerX))

            edg = list(listEdg)
            self.outputs['edgs'].StringsProperty = str([edg])
        else:
            self.outputs['edgs'].StringsProperty = str([[[]]])

        if 'pols' in self.outputs and len(self.outputs['pols'].links)>0:
            if not self.outputs['pols'].node.socket_value_update:
                self.inputs['pols'].node.update()

            listPlg = []
            for i in range(IntegerX-1):
                for j in range(IntegerY-1):
                    listPlg.append((IntegerX*j+i, IntegerX*j+i+1, IntegerX*j+i+IntegerX+1, IntegerX*j+i+IntegerX))
            plg = list(listPlg)
            self.outputs['pols'].StringsProperty = str([plg])
        else:
            self.outputs['pols'].StringsProperty = str([[[]]])
    
    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def make_vertices(self, delitelx, delitely, stepx, stepy, image_name):
        lenx = bpy.data.images[image_name].size[0]
        leny = bpy.data.images[image_name].size[1]
        #print ('image ', lenx, leny)
        if delitelx>lenx:
            delitelx=lenx
        if delitely>leny:
            delitely=leny
        x_ostatok = lenx%delitelx
        y_ostatok = leny%delitely
        #print ('img ostatok ', y_ostatok)
        xcoef = (lenx-x_ostatok)/delitelx
        ycoef = (leny-y_ostatok)/delitely
        #print ('img xy coefs ', xcoef,ycoef)
        imag = bpy.data.images[image_name].pixels
        pixy = []
        addition = 0
        for y in range(delitely):
            pixx = []
            addition = int(ycoef*y*4*lenx)
            for x in range(delitelx):
                # каждый пиксель кодируется RGBA, и записан строкой, без разделения на строки и столбцы.
                middle = (sum(imag[addition:addition+3])/3)*imag[addition+4]
                pixx.append(middle)
                addition += int(xcoef*4)
            pixy.append(pixx)
        #print ('img last addition ', addition)
        len_ver_x = len(pixy[0])
        len_ver_y = len(pixy)
        #print (pixy)
        overall_length = len_ver_x*len_ver_y
        vertices = []
        for y in range(len_ver_y):
            for x in range(len_ver_x):
                vertex = [x*stepx[x],y*stepy[y],pixy[y][x]]
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
