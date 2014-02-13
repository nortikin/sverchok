import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
from util import *

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

                #if type(self.inputs['Poligons'].links[0].from_socket) == StringsSocket:
                pols = SvGetSocketAnyType(self,self.inputs['Polygons'])
                
                #if type(self.inputs['Vertices'].links[0].from_socket) == VerticesSocket:
                vers = SvGetSocketAnyType(self,self.inputs['Vertices'])
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
                
                if 'Normals' in self.outputs and self.outputs['Normals'].links:
                    SvSetSocketAnyType(self,'Normals',normalsFORout)
            
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(VectorNormalNode)   
    
def unregister():
    bpy.utils.unregister_class(VectorNormalNode)

if __name__ == "__main__":
    register()