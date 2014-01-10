import bpy, bmesh, mathutils
from bpy.props import StringProperty
from node_s import *
from util import *

class SvObjSelected(bpy.types.Operator):
    """ G E T   SELECTED OBJECTS """
    bl_idname = "node.sverchok_object_insertion"
    bl_label = "Sverchok object selector"
    bl_options = {'REGISTER', 'UNDO'}
    
    name_objectin = StringProperty(name='name object in', description='it is name of reality')
    
    def enable(self, name_, name, handle):
        objects = []
        for o in bpy.context.selected_objects:
            objects.append(o.name)
        handle_write(name, objects)
        # временное решение с группой. надо решать, как достать имя группы узлов
        if len(bpy.data.node_groups) == 1:
            handle = handle_read(name)
            #print ('exec',name)
            bpy.data.node_groups[name_[1]].nodes[name_[0]].objects_local = str(handle[1])
    
    def disable(self, name, handle):
        if not handle[0]:
            return
        handle_delete(name)
    
    def execute(self, context):
        name_ = eval(self.name_objectin)
        name = str(name_[0]+name_[1])
        handle = handle_read(name)
        self.disable(name, handle)
        self.enable(name_, name, handle)
        return {'FINISHED'}
    
class ObjectsNode(Node, SverchCustomTreeNode):
    ''' Objects Input slot '''
    bl_idname = 'ObjectsNode'
    bl_label = 'Objects_in'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    #def object_select(self, context):
        #return [tuple(3 * [ob.name]) for ob in context.scene.objects if ob.type == 'MESH' or ob.type == 'EMPTY']
    objects_local = StringProperty(name='local objects in', description='objects, binded to current node', default='', update=updateNode)
    #ObjectProperty = EnumProperty(items = object_select, name = 'ObjectProperty')
    
    def init(self, context):
        self.outputs.new('VerticesSocket', "Vertices", "Vertices")
        self.outputs.new('StringsSocket', "Edges", "Edges")
        self.outputs.new('StringsSocket', "Polygons", "Polygons")
        self.outputs.new('MatrixSocket', "Matrixes", "Matrixes")
        
    def draw_buttons(self, context, layout):
        name_ = [self.name] + [self.id_data.name]
        name = str(name_[0]+name_[1])
        row = layout.row()
        row.scale_y = 4.0
        row.operator('node.sverchok_object_insertion', text='G E T').name_objectin = str(name_)
        handle = handle_read(name)
        if handle[0]:
            for o in handle[1]:
                layout.label(o)
        else:
            layout.label('--None--')

    def update(self):
        name_ = [self.name] + [self.id_data.name]
        name = str(name_[0]+name_[1])
        handle = handle_read(name)
        #print (handle)
        if self.objects_local and not handle[0]:
            handle_write(name, eval(self.objects_local))
        elif handle[0]:
            objs = handle[1]
            edgs_out = []
            vers_out = []
            pols_out = []
            mtrx_out = []
            for obj_ in objs: # names of objects
                edgs = []
                vers = []
                pols = []
                mtrx = []
                obj = bpy.data.objects[obj_] # objects itself
                if obj.type == 'EMPTY':
                    for m in obj.matrix_world:
                        mtrx.append(m[:])
                elif obj.type == 'CURVE':
                    for m in obj.matrix_world:
                        mtrx.append(m[:])
                else:
                    obj_data = obj.data
                    for m in obj.matrix_world:
                        mtrx.append(m[:])
                    for v in obj_data.vertices:
                        vers.append(v.co[:])
                    for edg in obj_data.edges:
                        edgs.append((edg.vertices[0],edg.vertices[1]))
                    for p in obj_data.polygons:
                        pols.append(p.vertices[:])
                    #print (vers, edgs, pols, mtrx)
                edgs_out.append(edgs)
                vers_out.append(vers)
                pols_out.append(pols)
                mtrx_out.append(mtrx)
            if vers_out[0]:
                if 'Vertices' in self.outputs and len(self.outputs['Vertices'].links)>0:
                    self.outputs['Vertices'].VerticesProperty = str(vers_out)
                    
                if 'Edges' in self.outputs and len(self.outputs['Edges'].links)>0:
                    self.outputs['Edges'].StringsProperty = str(edgs_out)
                    
                if 'Polygons' in self.outputs and len(self.outputs['Polygons'].links)>0:
                    self.outputs['Polygons'].StringsProperty = str(pols_out)
            
            if 'Matrixes' in self.outputs and len(self.outputs['Matrixes'].links)>0:
                self.outputs['Matrixes'].MatrixProperty = str(mtrx_out)
            #print ('матрёны: ', mtrx)
        #print (self.objects_local)
        if self.objects_local:
            self.use_custom_color=True
            self.color = (0,0.5,0.2)
        else:
            self.use_custom_color=True
            self.color = (0,0.1,0.05)
                
    def update_socket(self, context):
        self.update()



def register():
    bpy.utils.register_class(SvObjSelected)
    bpy.utils.register_class(ObjectsNode)
    
def unregister():
    bpy.utils.unregister_class(ObjectsNode)
    bpy.utils.unregister_class(SvObjSelected)

if __name__ == "__main__":
    register()



