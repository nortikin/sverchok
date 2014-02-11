import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *

class CentersPolsNode(Node, SverchCustomTreeNode):
    ''' Centers of polygons of mesh (not including matrixes, so apply scale-rot-loc ctrl+A) '''
    bl_idname = 'CentersPolsNode'
    bl_label = 'Centers polygons'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "Vertices", "Vertices")
        self.inputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('VerticesSocket',"Normals","Normals")
        self.outputs.new('MatrixSocket',"Centers","Centers")

    def update(self):
        # достаём два слота - вершины и полики
        if 'Centers' in self.outputs and self.outputs['Centers'].links or self.outputs['Normals'].links:
            if 'Polygons' in self.inputs and 'Vertices' in self.inputs and self.inputs['Polygons'].links and self.inputs['Vertices'].links:
                if not self.inputs['Polygons'].node.socket_value_update:
                    self.inputs['Polygons'].node.update()
                #if type(self.inputs['Polygons'].links[0].from_socket) == StringsSocket:
                pols_ = eval(self.inputs['Polygons'].links[0].from_socket.StringsProperty)
                #else:
                #    pols = []
                
                if not self.inputs['Vertices'].node.socket_value_update:
                    self.inputs['Vertices'].node.update()
                #if type(self.inputs['Vertices'].links[0].from_socket) == VerticesSocket:
                vers_ = eval(self.inputs['Vertices'].links[0].from_socket.VerticesProperty)
                #else:
                #    vers = []
                        
                #print ('Центрист.  полики, верики: ', pols, vers)
                
                # output
            
                # make mesh temp утилитарно - удалить в конце
                mat_collect = []
                normalsFORout = []
                for i_obj, vers in enumerate(vers_):
                    pols = pols_[i_obj]
                    mesh_temp = bpy.data.meshes.new('temp')
                    mesh_temp.from_pydata(vers,[],pols)
                    mesh_temp.update(calc_edges=True)
                    
                    # medians в векторах
                    medians = []
                    for p in pols:
                        v0 = Vector(vers[p[0]][:])
                        v1 = Vector(vers[p[1]][:])
                        v2 = Vector(vers[p[2]][:])
                        if len(p)>3:
                            v3 = Vector(vers[p[3]][:])
                            poi_2 = (v2+v3)/2
                        else:
                            poi_2 = v2
                            
                        poi_1 = (v0+v1)/2
                        vm = poi_2 - poi_1
                        medians.append(vm)
                    
                    # centers, normals - делает векторы из mesh temp
                    centrs = []
                    normals = []
                    normalsFORout_ = []
                    for p in mesh_temp.polygons:
                        centrs.append(Vector(p.center[:]))
                        normals.append(p.normal)
                        normalsFORout_.append(p.normal[:])
                    normalsFORout.append(normalsFORout_)
                    #print ('norm', normals, normalsFORout)
                    # centrs = mathutils.geometry.normal( lambda(vers[p[0]], vers[p[1]], vers[p[2]] for p in pols) ) # альтернатива
                    mat_collect_ = []
                    for i,c in enumerate(centrs):
                        mat_loc = Matrix.Translation(c)
                        aa = Vector((0,1e-6,1))
                        bb = Vector((normals[i][:]))
                        
                        vec = aa
                        q_rot = vec.rotation_difference(bb).to_matrix().to_4x4()
                        
                        vec2 = bb
                        q_rot2 = vec2.rotation_difference(aa).to_matrix().to_4x4()
                        
                        a = Vector((1e-6,1,0))* q_rot2
                        b = medians[i]
                        vec1 = a
                        q_rot1 = vec1.rotation_difference(b).to_matrix().to_4x4()
                        
                        M = mat_loc*q_rot1*q_rot
                        lM = []
                        
                        for j in M:
                            lM.append((j[:]))
                        # отдаётся параметр матрицы на сокет. просто присвоение матрицы
                        mat_collect_.append(lM)
                    mat_collect.extend(mat_collect_)
                        #print ( 'M'+ str(M) + '\n' + 'lM' + str(lM) + '\n' + 'qrot' + str(q_rot1) + '\n' )
                #print ( 'matrix: ' + str(mat_collect) )
                if not self.outputs['Centers'].node.socket_value_update:
                    self.outputs['Centers'].node.update()
                self.outputs['Centers'].MatrixProperty = str(mat_collect)
                # удаляем временный мусор
                bpy.data.meshes.remove(mesh_temp)
                if 'Normals' in self.outputs and len(self.outputs['Normals'].links)>0:
                    if not self.outputs['Normals'].node.socket_value_update:
                        self.outputs['Normals'].node.update()
                    self.outputs['Normals'].VerticesProperty = str(normalsFORout) 
            
            

    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(CentersPolsNode)   
    
def unregister():
    bpy.utils.unregister_class(CentersPolsNode)

if __name__ == "__main__":
    register()