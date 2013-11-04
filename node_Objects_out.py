import bpy, bmesh, mathutils
from util import *
from node_s import *

class ObjectsNodeOut(Node, SverchCustomTreeNode):
    ''' Objects Output '''
    bl_idname = 'ObjectsNodeOut'
    bl_label = 'Objects output'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('MatrixSocket', "Matrixes", "Matrixes")
        
    def draw_buttons(self, context, layout):
        pass
        
    def update(self):
        
        if 'vertices' in self.inputs and self.inputs['vertices'].links and len(self.inputs['vertices'].links)>0:
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()
            if self.inputs['vertices'].links[0].from_socket.VerticesProperty:
                vers = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
            else:
                vers = 0
            if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
                self.outputs['Vertices'].VerticesProperty = str(vers)
                        
        if 'edg_pol' in self.inputs and self.inputs['edg_pol'].links and len(self.inputs['edg_pol'].links)>0:
            if not self.inputs['edg_pol'].node.socket_value_update:
                self.inputs['edg_pol'].node.update()
            if self.inputs['edg_pol'].links[0].from_socket.StringsProperty:
                edg_pol = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
            else:
                edg_pol = 0
            if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
                self.outputs['Polygons'].StringsProperty = str(edg_pol)
            if "Edges" in self.outputs and len(self.outputs["Edges"].links)>0:
                self.outputs["Edges"].StringsProperty = str(edg_pol)
                
        if 'matrix' in self.inputs and self.inputs['matrix'].links and len(self.inputs['matrix'].links)>0:
            if not self.inputs['matrix'].node.socket_value_update:
                self.inputs['matrix'].node.update()
            if self.inputs['matrix'].links[0].from_socket.MatrixProperty:
                matrixes = eval(self.inputs['matrix'].links[0].from_socket.MatrixProperty)
            else:
                matrixes = 0
            if 'Matrixes' in self.outputs and len(self.outputs['Matrixes'].links)>0:
                self.outputs['Matrixes'].MatrixProperty = str(matrixes)
                
        if 'vertices' in self.inputs and 'edg_pol' in self.inputs and 'matrix' in self.inputs and \
            self.inputs['vertices'].links and self.inputs['edg_pol'].links and self.inputs['matrix'].links:
            self.makeobjects(vers, edg_pol, matrixes)
    
    def makeobjects(self, vers, edg_pol, mats):
        # inception
        if len(edg_pol[0][0]) == 2:
            edgs = edg_pol
            pols = []
            fht = max(a for a in max(edgs))
        elif len(edg_pol[0][0]) > 2:
            pols = edg_pol
            edgs = []
            fht = max(a for a in max(pols))
        vertices = Vector_generate(vers)
        matrixes = Matrix_generate(mats)
        #print('mats' + str(matrixes))
        objects = {}
        # objects = matrixes + mesh
        fhtagn = min(len(vertices), fht) - 1
        #print (fhtagn, vertices, matrixes, pols, edgs)
        for i, m in enumerate(matrixes):
            k = i
            if i > fhtagn:
                k = fhtagn
            v = vertices[k]
            #print (i)
            if edgs:
                e = edgs[k]
            else:
                e = edgs
            if pols:
                p = pols[k]
            else:
                p = pols
            objects[i] = self.makemesh(i,v,e,p,m)
        #print(objects)
        for ite in objects.values():
            #print ( ite )
            me = ite[1]
            ob = ite[0]
            me.update(calc_edges=True)
            bpy.context.scene.objects.link(ob)
            
    def makemesh(self,i,v,e,p,m):
        me = bpy.data.meshes.new('Sv_' + str(i))
        me.from_pydata(v, e, p)
        ob = bpy.data.objects.new('Sv_' + str(i), me)
        ob.location = m.translation
        ob.rotation_euler = m.to_euler()
        ob.scale = m.to_scale()
        ob.show_name = False
        ob.hide_select = False
        #print ([ob,me])
        return [ob,me]
    
    def update_socket(self, context):
        self.update()



def register():
    bpy.utils.register_class(ObjectsNodeOut)
    
def unregister():
    bpy.utils.unregister_class(ObjectsNodeOut)

if __name__ == "__main__":
    register()
