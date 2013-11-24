import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

# "coauthor": "Alessandro Zomparelli (sketchesofcode)"

class AdaptivePolsNode(Node, SverchCustomTreeNode):
    ''' Make spread one object on another adaptively polygons of mesh (not including matrixes, so apply scale-rot-loc ctrl+A) '''
    bl_idname = 'AdaptivePolsNode'
    bl_label = 'Adaptive Polygons'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    width_coef = bpy.props.FloatProperty(name='width_coef', description='with coefficient for sverchok adaptivepols donors size', default=1.0, max=3.0, min=0.5, update=updateNode)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "VersR", "VersR")
        self.inputs.new('StringsSocket', "PolsR", "PolsR")
        self.inputs.new('VerticesSocket', "VersD", "VersD")
        self.inputs.new('StringsSocket', "PolsD", "PolsD")
        self.inputs.new('StringsSocket', "Z_Coef", "Z_Coef")
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Poligons", "Poligons")
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "width_coef", text="donor width")
    
    def lerp(self, v1, v2, v3, v4, v):
        v12 = v1 + (v2-v1)*v[0] + ((v2-v1)/2)
        v43 = v4 + (v3-v4)*v[0] + ((v3-v4)/2)
        return v12 + (v43-v12)*v[1] + ((v43-v12)/2)
        
    def lerp2(self, v1, v2, v3, v4, v, x, y):
        v12 = v1 + (v2-v1)*v[0]*x + ((v2-v1)/2)
        v43 = v4 + (v3-v4)*v[0]*x + ((v3-v4)/2)
        return v12 + (v43-v12)*v[1]*y + ((v43-v12)/2)
        
    def lerp3(self, v1, v2, v3, v4, v, x, y, z):
        loc = self.lerp2(v1.co, v2.co, v3.co, v4.co, v, x, y)
        nor = self.lerp(v1.normal, v2.normal, v3.normal, v4.normal, v)
        nor.normalize()
        #print (loc, nor, v[2], z)
        return loc + nor*v[2]*z
    
    def update(self):
        # достаём два слота - вершины и полики
        if 'Vertices' in self.outputs and self.outputs['Vertices'].links:
            if self.inputs['PolsR'].links and self.inputs['VersR'].links and self.inputs['VersD'].links and self.inputs['PolsD'].links:
                if not self.inputs['PolsR'].node.socket_value_update:
                    self.inputs['PolsR'].node.update()
                if not self.inputs['VersR'].node.socket_value_update:
                    self.inputs['VersR'].node.update()
                if not self.inputs['VersD'].node.socket_value_update:
                    self.inputs['VersD'].node.update()
                if not self.inputs['PolsD'].node.socket_value_update:
                    self.inputs['PolsD'].node.update()
                if not self.inputs['Z_Coef'].node.socket_value_update:
                    self.inputs['Z_Coef'].node.update()
                if self.inputs['Z_Coef'].links:
                    z_coef = eval(self.inputs['Z_Coef'].links[0].from_socket.StringsProperty)[0]
                else:
                    z_coef = []
                
                
                
                polsR = eval(self.inputs['PolsR'].links[0].from_socket.StringsProperty)[0] # recipient one object [0]
                versR = eval(self.inputs['VersR'].links[0].from_socket.VerticesProperty)[0]  # recipient
                polsD = eval(self.inputs['PolsD'].links[0].from_socket.StringsProperty) # donor many objects [:]
                versD_ = eval(self.inputs['VersD'].links[0].from_socket.VerticesProperty) # donor
                versD = Vector_generate(versD_)
                ##### it is needed for normals of vertices
                new_me = bpy.data.meshes.new('recepient')
                new_me.from_pydata(versR, [], polsR)
                new_me.update(calc_edges=True)
                new_ve = new_me.vertices
                #print (new_ve[0].normal, 'normal')
                
                
                for i, vD in enumerate(versD):
                    
                    pD = polsD[i]
                    n_verts = len(vD)
                    n_faces = len(pD)
                    
                    xx = [x[0] for x in vD]
                    x0 = (self.width_coef) / (max(xx)-min(xx))
                    yy = [y[1] for y in vD]
                    y0 = (self.width_coef) / (max(yy)-min(yy))
                    zz = [z[2] for z in vD]
                    zzz = (max(zz)-min(zz))
                    if zzz:
                        z0 = 1 / zzz
                    else:
                        z0 = 0
                    #print (x0, y0, z0)
                    
                    vers_out = []
                    pols_out = []
                    
                    for j, pR in enumerate(polsR):
                        
                        last = len(pR)-1
                        vs = [new_ve[v] for v in pR]  # new_ve  - temporery data
                        if z_coef:
                            if j < len(z_coef):
                                z1 = z0 * z_coef[j]
                        else:
                            z1 = z0
                        
                        new_vers = []
                        new_pols = []
                        for v in vD:
                            new_vers.append(self.lerp3(vs[0], vs[1], vs[2], vs[last], v, x0, y0, z1))
                        for p in pD:
                            new_pols.append([id for id in p])
                        pols_out.append(new_pols)
                        vers_out.append(new_vers)
                    bpy.data.meshes.remove(new_me) # cleaning and washing
                    del(new_ve)
                        
                        
                        
                #print (Vector_degenerate(vers_out))
                
                if not self.outputs['Vertices'].node.socket_value_update:
                    self.outputs['Vertices'].node.update()
                output = Vector_degenerate(vers_out)
                #print (output)
                self.outputs['Vertices'].VerticesProperty = str(output)
                
                if 'Poligons' in self.outputs and len(self.outputs['Poligons'].links)>0:
                    if not self.outputs['Poligons'].node.socket_value_update:
                        self.outputs['Poligons'].node.update()
                    self.outputs['Poligons'].StringsProperty = str(pols_out) 
            
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(AdaptivePolsNode)   
    
def unregister():
    bpy.utils.unregister_class(AdaptivePolsNode)

if __name__ == "__main__":
    register()