import bpy
from node_s import *
from util import *
import math

class AreaNode(Node, SverchCustomTreeNode):
    ''' Area '''
    bl_idname = 'AreaNode'
    bl_label = 'Area'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    per_face = bpy.props.BoolProperty(name='per_face', default=True, update=updateNode)

    
    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('StringsSocket', "Area", "Area")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "per_face", text="Count faces")
        
    def update(self):
        # inputs
        if 'Vertices' in self.inputs and len(self.inputs['Vertices'].links)>0:
            if not self.inputs['Vertices'].node.socket_value_update:
                self.inputs['Vertices'].node.update()
            if self.inputs['Vertices'].links[0].from_socket.VerticesProperty:
                Vertices = eval(self.inputs['Vertices'].links[0].from_socket.VerticesProperty)
        else:
            Vertices = []

        if len(self.inputs['Polygons'].links)>0:
            if not self.inputs['Polygons'].node.socket_value_update:
                self.inputs['Polygons'].node.update()
            Polygons = eval(self.inputs['Polygons'].links[0].from_socket.StringsProperty)
        else:
            Polygons = []    

        # outputs
        if 'Area' in self.outputs and len(self.outputs['Area'].links)>0:
            if not self.outputs['Area'].node.socket_value_update:
               self.outputs['Area'].node.update()
            areas = []
            for i, obj in enumerate(Polygons):
                res = []
                for face in obj:
                    poly = []                 
                    for j in face:
                        poly.append(Vertices[i][j])
                    res.append(self.area(poly))  
   
                if self.per_face:
                    areas.extend(res)
                else:
                    areas.append(math.fsum(res))
                   
            self.outputs['Area'].StringsProperty = str([areas])
    
    #determinant of matrix a
    def det(self, a):
        return a[0][0]*a[1][1]*a[2][2] + a[0][1]*a[1][2]*a[2][0] + a[0][2]*a[1][0]*a[2][1] - a[0][2]*a[1][1]*a[2][0] - a[0][1]*a[1][0]*a[2][2] - a[0][0]*a[1][2]*a[2][1]

    #unit normal vector of plane defined by points a, b, and c
    def unit_normal(self, a, b, c):
        x = self.det([[1,a[1],a[2]],
                      [1,b[1],b[2]],
                      [1,c[1],c[2]]])
        y = self.det([[a[0],1,a[2]],
                      [b[0],1,b[2]],
                      [c[0],1,c[2]]])
        z = self.det([[a[0],a[1],1],
                      [b[0],b[1],1],
                      [c[0],c[1],1]])
        magnitude = (x**2 + y**2 + z**2)**.5
        return (x/magnitude, y/magnitude, z/magnitude)

    #dot product of vectors a and b
    def dot(self, a, b):
        return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

    #cross product of vectors a and b
    def cross(self, a, b):
        x = a[1] * b[2] - a[2] * b[1]
        y = a[2] * b[0] - a[0] * b[2]
        z = a[0] * b[1] - a[1] * b[0]
        return (x, y, z)

    #area of polygon poly
    def area(self, poly):
        if len(poly) < 3: # not a plane - no area
            return 0

        total = [0, 0, 0]
        for i in range(len(poly)):
            vi1 = poly[i]
            if i is len(poly)-1:
                vi2 = poly[0]
            else:
                vi2 = poly[i+1]
            prod = self.cross(vi1, vi2)
            total[0] += prod[0]
            total[1] += prod[1]
            total[2] += prod[2]
        result = self.dot(total, self.unit_normal(poly[0], poly[1], poly[2]))
        return abs(result/2)

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(AreaNode)
    
def unregister():
    bpy.utils.unregister_class(AreaNode)

if __name__ == "__main__":
    register()
