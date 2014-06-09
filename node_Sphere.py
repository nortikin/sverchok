import bpy
from node_s import *
from util import *
from math import sin, cos

def sphere_verts(U, V, Radius):
    theta  = radians(360/U)
    phi = radians(180/(V-1))
    pts = [[0,0,Radius]]
    for i in range(1,V-1):
        sin_phi_i =sin(phi*i)
        for j in range(U):
            X = Radius*cos(theta*j)*sin_phi_i
            Y = Radius*sin(theta*j)*sin_phi_i 
            Z = Radius*cos(phi*i)
            pts.append([X,Y,Z])
    pts.append([0,0, -Radius])
    return pts  

def sphere_edges(U,V):
    nr_pts = U*V-(U-1)*2
    listEdg = []
    for i in range(V-2):
        listEdg.extend([[j+1+U*i, j+2+U*i] for j in range(U-1)])
        listEdg.append([U*(i+1), U*(i+1)-U+1])
    listEdg.extend([[i+1, i+1+U] for i in range(U*(V-3))])
    listEdg.extend([[0, i+1] for i in range(U)])
    listEdg.extend([[nr_pts-1, i+nr_pts-U-1] for i in range(U)])        
    listEdg.reverse()
    return listEdg
    
def sphere_faces(U,V):
    nr_pts = U*V-(U-1)*2
    listPln = []
    for i in range(V-3):
        listPln.append([U*i+2*U, 1+U*i+U, 1+U*i,  U*i+U])
        listPln.extend([[1+U*i+j+U, 2+U*i+j+U, 2+U*i+j, 1+U*i+j] for j in range(U-1) ])

    for i in range(U-1):
        listPln.append([1+i, 2+i, 0])
        listPln.append([i+nr_pts-U, i+nr_pts-1-U, nr_pts-1])
    listPln.append([U, 1, 0])
    listPln.append([nr_pts-1-U, nr_pts-2, nr_pts-1])
    return listPln

 

class SphereNode(Node, SverchCustomTreeNode):
    ''' Sphere '''
    bl_idname = 'SphereNode'
    bl_label = 'Sphere'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    rad_ = bpy.props.FloatProperty(name = 'Radius', description='Radius', default=1.0, options={'ANIMATABLE'}, update=updateNode)
    U_ = bpy.props.IntProperty(name = 'U', description='U', default=24, min=3, options={'ANIMATABLE'}, update=updateNode)
    V_ = bpy.props.IntProperty(name = 'V', description='V', default=24, min=3, options={'ANIMATABLE'}, update=updateNode)

    def init(self, context):
        self.inputs.new('StringsSocket', "Radius").prop_name = 'rad_'
        self.inputs.new('StringsSocket', "U").prop_name = 'U_'
        self.inputs.new('StringsSocket', "V").prop_name = 'V_'
        
        self.outputs.new('VerticesSocket', "Vertices")
        self.outputs.new('StringsSocket', "Edges")
        self.outputs.new('StringsSocket', "Polygons")
    
    def draw_buttons(self, context, layout):
        pass
        #layout.prop(self, "rad_", text="Radius")
        #layout.prop(self, "U_", text="U")
        #layout.prop(self, "V_", text="V")

    def update(self):
        # inputs
        if not 'Polygons' in self.outputs:
            return
            
        Radius = self.inputs['Radius'].sv_get()[0]
        U = [max(int(u),3) for u in self.inputs['U'].sv_get()[0]]
        V = [max(int(v),3) for v in self.inputs['V'].sv_get()[0]]

        params = match_long_repeat([U,V,Radius])
        
        # outputs
        if self.outputs['Vertices'].links:
            verts = [sphere_verts(u,v,r) for u,v,r in zip(*params)]
            SvSetSocketAnyType(self,'Vertices',verts)

        if self.outputs['Edges'].links:
            edges = [sphere_edges(u,v) for u,v,r in zip(*params)]
            SvSetSocketAnyType(self, 'Edges', edges)

        if self.outputs['Polygons'].links: 
            faces = [sphere_faces(u,v) for u,v,r in zip(*params)]
            SvSetSocketAnyType(self, 'Polygons', faces)



    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SphereNode)
    
def unregister():
    bpy.utils.unregister_class(SphereNode)

if __name__ == "__main__":
    register()
