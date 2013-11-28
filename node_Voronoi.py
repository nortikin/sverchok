import bpy
from node_s import *
from util import *
from types import *

class VoronoiNode(Node, SverchCustomTreeNode):
    ''' Voronoi line '''
    bl_idname = 'VoronoiNode'
    bl_label = 'Voronoi'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    sizeX_ = bpy.props.FloatProperty(name = 'sizeX', description='SizeX', default=1.0, min=0.1, max=6, options={'ANIMATABLE'}, update=updateNode)
    sizeY_ = bpy.props.FloatProperty(name = 'sizeY', description='SizeY', default=1.0, min=0.1, options={'ANIMATABLE'}, update=updateNode)
    sizeZ_ = bpy.props.FloatProperty(name = 'sizeZ', description='SizeZ', default=1.0, min=0.1, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        #self.inputs.new('StringsSocket', "SizeX", "SizeX")
        #self.inputs.new('StringsSocket', "SizeY", "SizeY")
        #self.inputs.new('StringsSocket', "SizeZ", "SizeZ")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "sizeX_", text="SizeX")
        layout.prop(self, "sizeY_", text="SizeY")
        layout.prop(self, "sizeZ_", text="SizeZ")

    def update(self):
        # inputs
        if len(self.outputs['Edges'].links)>0 or len(self.outputs['Vertices'].links)>0:
            if len(self.inputs['Level'].links)>0:
                if not self.inputs['Level'].node.socket_value_update:
                    self.inputs['Level'].node.update()
                Integer = int(eval(self.inputs['Level'].links[0].from_socket.StringsProperty)[0][0])
            else:
                Integer = self.level_
    
            if len(self.inputs['Size'].links)>0:
                if not self.inputs['Size'].node.socket_value_update:
                    self.inputs['Size'].node.update()
                Step = eval(self.inputs['Size'].links[0].from_socket.StringsProperty)[0][0]
            else:
                Step = self.size_
            

        # outputs
        if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
            if not self.outputs['Vertices'].node.socket_value_update:
                self.outputs['Vertices'].node.update()
            
            verts = self.hilbert(0.0, 0.0, Step*1.0, 0.0, 0.0, Step*1.0, Integer)
            
            self.outputs['Vertices'].VerticesProperty = str([verts])

        if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
            if not self.outputs['Edges'].node.socket_value_update:
                self.outputs['Edges'].node.update()

            listEdg = []
            r = len(verts)-1
            for i in range(r):
                listEdg.append((i, i+1))

            edg = list(listEdg)
            self.outputs['Edges'].StringsProperty = str([edg])

    def voronoi(self, xbox, yboy, zboz, vertices):
    	#image = Image.new("RGB", (width, height))
    	#putpixel = image.putpixel
    	#imgx, imgy = image.size
    	nx = []
    	ny = []
    	nz = []
    	for vert in vertices:
    		nx.append(vert[0])
    		ny.append(vert[1])
    		nz.append(vert[2])
    		
    	for y in range(imgy):
    		for x in range(imgx):
    			dmin = math.hypot(imgx-1, imgy-1)
    			j = -1
    			for i in range(num_cells):
    				d = math.hypot(nx[i]-x, ny[i]-y)
    				if d < dmin:
    					dmin = d
    					j = i
    			#putpixel((x, y), (nr[j], ng[j], nb[j]))
    	#image.save("VoronoiDiagram.png", "PNG")
            #image.show()

    def fullList(self, l, count):
        d = count - len(l)
        if d > 0:
            l.extend([l[-1] for a in range(d)])
        return
    
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(VoronoiNode)
    
def unregister():
    bpy.utils.unregister_class(VoronoiNode)

if __name__ == "__main__":
    register()