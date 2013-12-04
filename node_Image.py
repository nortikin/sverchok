import bpy
from node_s import *
from util import *

class ImageNode(Node, SverchCustomTreeNode):
    ''' Image '''
    bl_idname = 'ImageNode'
    bl_label = 'Image'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def images(self, context):
        return [tuple(3 * [im.name]) for im in bpy.data.images]
    name_image = EnumProperty(items=images, name='images')
    R = bpy.props.FloatProperty(name='R', description='R', default=0.30, min=0, max=1, options={'ANIMATABLE'}, update=updateNode)
    G = bpy.props.FloatProperty(name='G', description='G', default=0.59, min=0, max=1, options={'ANIMATABLE'}, update=updateNode)
    B = bpy.props.FloatProperty(name='B', description='B', default=0.11, min=0, max=1, options={'ANIMATABLE'}, update=updateNode)
    Xvecs = bpy.props.IntProperty(name='Xvecs', description='Xvecs', default=10, min=2, max=100, options={'ANIMATABLE'}, update=updateNode)
    Yvecs = bpy.props.IntProperty(name='Yvecs', description='Yvecs', default=10, min=2, max=100, options={'ANIMATABLE'}, update=updateNode)
    Xstep = bpy.props.FloatProperty(name='Xstep', description='Xstep', default=1.0, min=0.01, max=100, options={'ANIMATABLE'}, update=updateNode)
    Ystep = bpy.props.FloatProperty(name='Ystep', description='Ystep', default=1.0, min=0.01, max=100, options={'ANIMATABLE'}, update=updateNode)
    #name_image = bpy.props.StringProperty(name='image_name', description='image name', default='', update=updateNode)
    
    def init(self, context):
        self.inputs.new('StringsSocket', "vecs X", "vecs X")
        self.inputs.new('StringsSocket', "vecs Y", "vecs Y")
        self.inputs.new('StringsSocket', "Step X", "Step X")
        self.inputs.new('StringsSocket', "Step Y", "Step Y")
        self.outputs.new('VerticesSocket', "vecs", "vecs")
        self.outputs.new('StringsSocket', "edgs", "edgs")
        self.outputs.new('StringsSocket', "pols", "pols")
    
    def draw_buttons(self, context, layout):
        row = layout.column_flow(columns=1,align=True)
        row.prop(self, "Xvecs", text="vectors X")
        row.prop(self, "Yvecs", text="vectors Y")
        row = layout.column_flow(columns=1,align=True)
        row.prop(self, "Xstep", text="step X")
        row.prop(self, "Ystep", text="step Y")
        row = layout.row(align=True)
        row.scale_x=10.0
        row.prop(self, "R", text="R")
        row.prop(self, "G", text="G")
        row.prop(self, "B", text="B")
        layout.prop(self, "name_image", text="image")

    def update(self):
        # inputs
        if len(self.inputs['vecs X'].links)>0:
            if not self.inputs['vecs X'].node.socket_value_update:
                self.inputs['vecs X'].node.update()
            IntegerX = min(int(eval(self.inputs['vecs X'].links[0].from_socket.StringsProperty)[0][0]),100)
        else:
            IntegerX = int(self.Xvecs)

        if len(self.inputs['vecs Y'].links)>0:
            if not self.inputs['vecs Y'].node.socket_value_update:
                self.inputs['vecs Y'].node.update()
            IntegerY = min(int(eval(self.inputs['vecs Y'].links[0].from_socket.StringsProperty)[0][0]),100)
        else:
            IntegerY = int(self.Yvecs)

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
            
            out = self.make_vertices(IntegerX-1, IntegerY-1, StepX, StepY, self.name_image)
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
        if delitelx>lenx:
            delitelx=lenx
        if delitely>leny:
            delitely=leny
        R, G, B = self.R, self.G, self.B
        xcoef = lenx//delitelx
        ycoef = leny//delitely
        imag = bpy.data.images[image_name].pixels
        vertices = []
        addition = 0
        for y in range(delitely+1):
            addition = int(ycoef*y*4*lenx)
            for x in range(delitelx+1):
                 # каждый пиксель кодируется RGBA, и записан строкой, без разделения на строки и столбцы.
                middle = (imag[addition]*R+imag[addition+1]*G+imag[addition+2]*B)*imag[addition+3]
                vertex = [x*stepx[x],y*stepy[y],middle]
                vertices.append(vertex)
                addition += int(xcoef*4)
        return vertices
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(ImageNode)
    
def unregister():
    bpy.utils.unregister_class(ImageNode)

if __name__ == "__main__":
    register()
