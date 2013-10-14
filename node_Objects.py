import bpy, bmesh, mathutils
from node_s import *

class ObjectsNode(Node, SverchCustomTreeNode):
    ''' Objects Input slot '''
    bl_idname = 'ObjectsNode'
    bl_label = 'Objects input'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def object_select(self, context):
        return [tuple(3 * [ob.name]) for ob in context.scene.objects if ob.type == 'MESH']
            
    ObjectProperty = EnumProperty(items = object_select, name = 'ObjectProperty')
    
    def init(self, context):
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('MatrixSocket', "Matrixes", "Matrixes")
        
    def draw_buttons(self, context, layout):
        layout.prop(self, "ObjectProperty", text="Object", icon='OBJECT_DATA')

    def update(self):
        if self.ObjectProperty:
            obj = bpy.data.objects[self.ObjectProperty]
            obj_data = obj.data
            edgs = []
            vers = []
            pols = []
            mtrx = []
            for m in obj.matrix_world:
                mtrx.append(m[:])
            for v in obj_data.vertices:
                vers.append(v.co[:])
            for edg in obj_data.edges:
                edgs.append((edg.vertices[0],edg.vertices[1]))
            for p in obj_data.polygons:
                pols.append(p.vertices[:])
            #print (vers, edgs, pols, mtrx)
            
            if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
                self.outputs['Vertices'].VerticesProperty = str([vers, ])
                
            if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
                self.outputs['Edges'].StringsProperty = str([edgs, ])
                
            if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
                self.outputs['Polygons'].StringsProperty = str([pols, ])
            
            if 'Matrixes' in self.outputs and len(self.outputs['Matrixes'].links)>0:
                self.outputs['Matrixes'].MatrixProperty = str([mtrx, ])
            #print ('матрёны: ', mtrx)
                
    def update_socket(self, context):
        self.update()



def register():
    bpy.utils.register_class(ObjectsNode)
    
def unregister():
    bpy.utils.unregister_class(ObjectsNode)

if __name__ == "__main__":
    register()



