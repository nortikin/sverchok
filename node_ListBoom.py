import bpy
from node_s import *
from util import *


class ListBoomNode(Node, SverchCustomTreeNode):
    ''' Destroy object to many object of polygons '''
    bl_idname = 'ListBoomNode'
    bl_label = 'ListBoom'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def init(self, context):
        self.inputs.new('VerticesSocket', "vertices", "vertices")
        self.inputs.new('StringsSocket', 'edg_pol', 'edg_pol')
        self.outputs.new('VerticesSocket', 'vertices', 'vertices')
        self.outputs.new('StringsSocket', 'edg_pol', 'edg_pol')
    
    
    def draw_buttons(self, context, layout):
        pass
    
    def update(self):
        # inputs
        if 'vertices' in self.inputs and self.inputs['vertices'].links and \
                'edg_pol' in self.inputs and self.inputs['edg_pol'].links:
            vertices = eval(self.inputs['vertices'].links[0].from_socket.VerticesProperty)
            edgs_pols = eval(self.inputs['edg_pol'].links[0].from_socket.StringsProperty)
        
        if 'vertices' in self.outputs and self.outputs['vertices'].links or \
                'edg_pol' in self.outputs and self.outputs['edg_pol'].links:
            vert_out = []
            edpo_out = []
            for k, ob in enumerate(edgs_pols):
                for ep in ob:
                    new_vers = []
                    new_edpo = []
                    for i, index in enumerate(ep):
                        new_vers.append(vertices[k][index])
                        new_edpo.append(i)
                    vert_out.append(new_vers)
                    edpo_out.append([new_edpo])
            
            if len(self.outputs['vertices'].links)>0:
                if not self.outputs['vertices'].node.socket_value_update:
                    self.outputs['vertices'].node.update()
                self.outputs['vertices'].links[0].from_socket.VerticesProperty =  str(vert_out)
            if len(self.outputs['edg_pol'].links)>0:
                if not self.outputs['edg_pol'].node.socket_value_update:
                    self.outputs['edg_pol'].node.update()
                self.outputs['edg_pol'].links[0].from_socket.StringsProperty = str(edpo_out)

def register():
    bpy.utils.register_class(ListBoomNode)
    
def unregister():
    bpy.utils.unregister_class(ListBoomNode)

if __name__ == "__main__":
    register()