import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *

class VectorNormalNode(Node, SverchCustomTreeNode):
    ''' Find Vector's normals '''
    bl_idname = 'VectorNormalNode'
    bl_label = 'Vector Normal'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('VerticesSocket',"Normals","Normals")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Centers' in self.outputs and self.outputs['Centers'].links or self.outputs['Normals'].links:
            if 'Polygons' in self.inputs and 'Vertices' in self.inputs and self.inputs['Polygons'].links and self.inputs['Vertices'].links:
                if not self.inputs['Polygons'].node.socket_value_update:
                    self.inputs['Polygons'].node.update()
                #if type(self.inputs['Poligons'].links[0].from_socket) == StringsSocket:
                pols = eval(self.inputs['Polygons'].links[0].from_socket.StringsProperty)
                
                
                if not self.inputs['Vertices'].node.socket_value_update:
                    self.inputs['Vertices'].node.update()
                #if type(self.inputs['Vertices'].links[0].from_socket) == VerticesSocket:
                vers = eval(self.inputs['Vertices'].links[0].from_socket.VerticesProperty)
                
                normalsFORout = []
                for i, obj in enumerate(vers):
                    mesh_temp = bpy.data.meshes.new('temp')
                    mesh_temp.from_pydata(obj,[],pols[i])
                    mesh_temp.update(calc_edges=True)
                    tempobj = []
                    for v in mesh_temp.vertices:
                        tempobj.append(v.normal[:])
                    normalsFORout.append(tempobj)
                    bpy.data.meshes.remove(mesh_temp)
                #print (normalsFORout)
                
                if 'Normals' in self.outputs and len(self.outputs['Normals'].links)>0:
                    if not self.outputs['Normals'].node.socket_value_update:
                        self.outputs['Normals'].node.update()
                    self.outputs['Normals'].VerticesProperty = str(normalsFORout) 
            
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(VectorNormalNode)   
    
def unregister():
    bpy.utils.unregister_class(VectorNormalNode)

if __name__ == "__main__":
    register()