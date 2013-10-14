import bpy, bmesh, mathutils
from mathutils import Matrix
from util import *
from node_s import *

#global cache_viewer_slot1, cache_viewer_slot2, cache_viewer_slot3
cache_viewer_slot1 = {} #{'veriable':'None \n'}
cache_viewer_slot2 = {} #{'veriable':'None \n'}
cache_viewer_slot3 = {} #{'veriable':'None \n'}

class SverchokViewer(bpy.types.Operator):
    """Sverchok viewer"""
    bl_idname = "node.sverchok_viewer_button"
    bl_label = "Sverchok viewer"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        global cache_viewer_slot1
        global cache_viewer_slot2
        global cache_viewer_slot3
        
        texts = bpy.data.texts.items()
        exists = False
        for t in texts:
            if bpy.data.texts[t[0]].name == 'Sverchok_viewer':
                exists = True
                break
        bpy.context.area.type = 'TEXT_EDITOR'
        if not exists:
            bpy.ops.text.new()
            texts_new = bpy.data.texts.items()
            for t in texts_new:
                if t not in texts:
                    bpy.data.texts[t[0]].name = 'Sverchok_viewer'
        bpy.ops.text.select_all()
        podpis = '\n' + 'Sverchok forever' + '\n' + 'edg_pol сокет универсальный, на самом деле,' + '\n' + ' туда можно будет пихать непихуемое' + '\n' + 'Наверное его назвать надо просто data или как-то так.'
        for_file = 'vertices: \n' + cache_viewer_slot1['veriable'] \
            + cache_viewer_slot2['type'] + cache_viewer_slot2['veriable'] \
            + 'matrixes: \n' + cache_viewer_slot3['veriable'] + podpis
        bpy.data.texts['Sverchok_viewer'].from_string(for_file)
        bpy.context.area.type = 'NODE_EDITOR'
        #print (cache_viewer_slot1['veriable'], cache_viewer_slot2['veriable'], cache_viewer_slot3['veriable'])
        cache_viewer_slot1['veriable'] = 'None \n'
        cache_viewer_slot2['veriable'] = 'None \n'
        cache_viewer_slot3['veriable'] = 'None \n'
        return {'FINISHED'}

class ViewerNode_text(Node, SverchCustomTreeNode):
    ''' Viewer Node text '''
    bl_idname = 'ViewerNode_text'
    bl_label = 'Viewer Node text'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
        
    def draw_buttons(self, context, layout):
        layout.operator('node.sverchok_viewer_button', text='view')
    
    def update(self):
        # vertices socket
        global cache_viewer_slot1
        global cache_viewer_slot2
        global cache_viewer_slot3
        cache_viewer_slot1['veriable'] = 'None \n'
        cache_viewer_slot2['veriable'] = 'None \n'
        cache_viewer_slot2['type'] = 'unknown data: \n'
        cache_viewer_slot3['veriable'] = 'None \n'
        if len(self.inputs['vertices'].links)>0:
            if not self.inputs['vertices'].node.socket_value_update:
                self.inputs['vertices'].node.update()
            if type(self.inputs['vertices'].links[0].from_socket) == bpy.types.VerticesSocket:
                line_str = self.inputs['vertices'].links[0].from_socket.VerticesProperty
                a = readFORviewer_sockets_data(line_str) # from util
                cache_viewer_slot1['veriable'] = a
                print ('viewer text input1')
        # edges/faces socket
        if len(self.inputs['edg_pol'].links)>0:
            if not self.inputs['edg_pol'].node.socket_value_update:
                self.inputs['edg_pol'].node.update()
            if type(self.inputs['edg_pol'].links[0].from_socket) == bpy.types.StringsSocket:
                line_str = self.inputs['edg_pol'].links[0].from_socket.StringsProperty
                if type(eval(line_str)[0][0]) == list:
                    if len(eval(line_str)[0][0]) > 2:
                        cache_viewer_slot2['type'] = 'polygons: \n'
                    else:
                        cache_viewer_slot2['type'] = 'edges: \n'
                else:
                    cache_viewer_slot2['type'] = 'unknown data: \n'
                b = readFORviewer_sockets_data(line_str) # from util
                cache_viewer_slot2['veriable'] = str(b)
                print ('viewer text input2')
        # matrix socket
        if len(self.inputs['matrix'].links)>0:
            if not self.inputs['matrix'].node.socket_value_update:
                self.inputs['matrix'].node.update()
            if type(self.inputs['matrix'].links[0].from_socket) == bpy.types.MatrixSocket:
                matrix = self.inputs['matrix'].links[0].from_socket.MatrixProperty
                c = readFORviewer_sockets_data(matrix) # from util
                cache_viewer_slot3['veriable'] = str(c)
                print ('viewer text input3')
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(SverchokViewer)
    bpy.utils.register_class(ViewerNode_text)
    
def unregister():
    bpy.utils.unregister_class(ViewerNode_text)
    bpy.utils.unregister_class(SverchokViewer)

if __name__ == "__main__":
    register()