import bpy, bmesh, mathutils
from mathutils import Vector, Matrix
from node_s import *
import Viewer_draw
from Viewer_draw import *



class ViewerNode(Node, SverchCustomTreeNode):
    ''' ViewerNode '''
    bl_idname = 'ViewerNode'
    bl_label = 'Viewer Node'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    Vertex_show = bpy.props.BoolProperty(name='Vertex_show', description='Show or not vertices', default=True)
    
    def init(self, context):
        self.inputs.new('VerticesSocket', 'vertices', 'vertices')
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.inputs.new('MatrixSocket', 'matrix', 'matrix')
    
    def draw_buttons(self, context, layout):
        layout.prop(self, "Vertex_show", text="Vertex show")
        
    def update(self):
        if 'vertices' in self.inputs and self.inputs['vertices'].links:
            callback_disable(self.name)
            if len(self.inputs['vertices'].links)>0:
                if not self.inputs['vertices'].node.socket_value_update:
                    self.inputs['vertices'].node.update()
                if self.inputs['vertices'].links[0].from_socket.VerticesProperty:
                    propv = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
                    cache_viewerdraw_slot1 = propv
            else:
                cache_viewerdraw_slot1 = []
                            
            if 'edg_pol' in self.inputs and self.inputs['edg_pol'].links and len(self.inputs['edg_pol'].links)>0:
                if not self.inputs['edg_pol'].node.socket_value_update:
                    self.inputs['edg_pol'].node.update()
                if self.inputs['edg_pol'].links[0].from_socket.StringsProperty:
                    prope = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
                    cache_viewerdraw_slot2 = prope
            else:
                cache_viewerdraw_slot2 = []
                    
            if 'matrix' in self.inputs and self.inputs['matrix'].links and len(self.inputs['matrix'].links)>0:
                if not self.inputs['matrix'].node.socket_value_update:
                    self.inputs['matrix'].node.update()
                if self.inputs['matrix'].links[0].from_socket.MatrixProperty:
                    propm = eval(self.inputs['matrix'].links[0].from_socket.MatrixProperty)
                    cache_viewerdraw_slot3 = propm
            else:
                cache_viewerdraw_slot3 = []
            if cache_viewerdraw_slot1 and cache_viewerdraw_slot2 and cache_viewerdraw_slot3:
                callback_enable(self.name, cache_viewerdraw_slot1, cache_viewerdraw_slot2, cache_viewerdraw_slot3, self.Vertex_show)
        if not self.inputs['vertices'].links:
            callback_disable(self.name)
    
    def update_socket(self, context):
        self.update()

def register():
    bpy.utils.register_class(ViewerNode)
    
def unregister():
    bpy.utils.unregister_class(ViewerNode)

if __name__ == "__main__":
    register()