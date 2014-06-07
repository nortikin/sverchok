import bpy
from node_s import *
from util import *
from math import sin, cos

def cylinder_vertices(Subd, Vertices, Height, RadiusBot, RadiusTop, Separate):
    theta = 360/Vertices
    heightSubd = Height/(Subd+1)
    X = []
    Y = []
    Z = []
    for i in range(Subd+2):
        radius = RadiusBot - ((RadiusBot-RadiusTop)/(Subd+1))*i
        for j in range(Vertices):
            X.append(radius*cos(radians(theta*j)))
            Y.append(radius*sin(radians(theta*j)))
            Z.append(heightSubd*i)

    points = list(sv_zip(X,Y,Z))
    if Separate:
        out=[]
        for y in range(Vertices):
            out_=[]
            for x in range(Subd+2):
                out_.append(points[Subd+2*y+x])
            out.append(out_)
        points = out
    return points

def cylinder_edges(Subd, Vertices):
    listEdg = []
    for i in range(Subd+2):
        for j in range(Vertices-1):
            listEdg.append([j+Vertices*i, j+1+Vertices*i])
        listEdg.append([Vertices-1+Vertices*i, 0+Vertices*i])
    for i in range(Subd+1):
        for j in range(Vertices):
            listEdg.append([j+Vertices*i, j+Vertices+Vertices*i])
            
    return listEdg
    
def cylinder_faces(Subd,Vertices,Cap):
    listPlg = []
    for i in range(Subd+1):
        for j in range(Vertices-1):
            listPlg.append([j+Vertices*i, j+1+Vertices*i, j+1+Vertices*i+Vertices, j+Vertices*i+Vertices])
        listPlg.append([Vertices-1+Vertices*i, 0+Vertices*i, 0+Vertices*i+Vertices, Vertices-1+Vertices*i+Vertices])
    if Cap:
        capBot = []
        capTop = []
        for i in range(Vertices):
            capBot.append(i)
            capTop.append(Vertices*(Subd+1)+i)
        capBot.reverse()
        listPlg.append(capBot)
        listPlg.append(capTop)
    return listPlg
            

class CylinderNode(Node, SverchCustomTreeNode):
    ''' Cylinder '''
    bl_idname = 'CylinderNode'
    bl_label = 'Cylinder'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    radTop_ = bpy.props.FloatProperty(name = 'Radius Top', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    radBot_ = bpy.props.FloatProperty(name = 'Radius Bottom', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    vert_ = bpy.props.IntProperty(name = 'Vertices', default=32, min=3, options={'ANIMATABLE'}, update=updateNode)
    height_ = bpy.props.FloatProperty(name = 'Height', default=2.0, options={'ANIMATABLE'}, update=updateNode)
    subd_ = bpy.props.IntProperty(name = 'Subdivisions', default=0, min=0,options={'ANIMATABLE'}, update=updateNode)
    cap_ = bpy.props.BoolProperty(name = 'Caps', default=True, options={'ANIMATABLE'}, update=updateNode)
    Separate = bpy.props.BoolProperty(name = 'Separate', description='Separate UV coords', default=False, update=updateNode)
 
    def init(self, context):
        self.inputs.new('StringsSocket', "RadTop").prop_name = 'radTop_'
        self.inputs.new('StringsSocket', "RadBot").prop_name = 'radBot_'
        self.inputs.new('StringsSocket', "Vertices").prop_name = 'vert_'
        self.inputs.new('StringsSocket', "Height").prop_name = 'height_'
        self.inputs.new('StringsSocket', "Subdivisions").prop_name = 'subd_'
      
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
    
    def draw_buttons(self, context, layout):
        row = layout.row(align=True)
        row.prop(self, "Separate", text="Separate")
        row.prop(self, "cap_", text="Caps")
        
    def update(self):
        if not 'Polygons' in self.outputs:
            return
        # inputs
        
        inputs = self.inputs
        
        RadiusTop = inputs['RadTop'].sv_get()[0]
        RadiusBot = inputs['RadBot'].sv_get()[0]
        Vertices = [max(int(v),3) for v in inputs['Vertices'].sv_get()[0]]
        Height = inputs['Height'].sv_get()[0]
        Sub = [max(int(s),0) for s in inputs['Subdivisions'].sv_get()[0]]
        params = match_long_repeat([Sub, Vertices, Height, RadiusBot, RadiusTop])
        # outputs
        if self.outputs['Vertices'].links:
            
            points = [cylinder_vertices(s,v,h,rb,rt,self.Separate) 
                        for s,v,h,rb,rt in zip(*params)]
            SvSetSocketAnyType(self, 'Vertices',points)
                
        if self.outputs['Edges'].links:
            edges = [cylinder_edges(s,v)
                        for s,v,h,rb,rt in zip(*params)]
            SvSetSocketAnyType(self, 'Edges',edges)

        if self.outputs['Polygons'].links:
            faces = [cylinder_faces(s,v,self.cap_)
                        for s,v,h,rb,rt in zip(*params)]
            SvSetSocketAnyType(self, 'Polygons',faces)

    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(CylinderNode)
    
def unregister():
    bpy.utils.unregister_class(CylinderNode)

if __name__ == "__main__":
    register()
