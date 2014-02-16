import bpy
from node_s import *
from util import *

class SvFrameInfoNode(Node, SverchCustomTreeNode):
    ''' Frame Info '''
    bl_idname = 'SvFrameInfoNode'
    bl_label = 'Frame Info'
    bl_icon = 'OUTLINER_OB_EMPTY'
        
    def init(self, context):
        self.outputs.new('StringsSocket', "Current Frame", "Current Frame")
        self.outputs.new('StringsSocket', "Start Frame", "Start Frame")
        self.outputs.new('StringsSocket', "End Frame", "End Frame")

    def update(self):
        # outputs
        if 'Current Frame' in self.outputs and self.outputs['Current Frame'].links:
            SvSetSocketAnyType(self, 'Current Frame',[[bpy.context.scene.frame_current]])
        if 'Start Frame' in self.outputs and self.outputs['Start Frame'].links:
            SvSetSocketAnyType(self, 'Start Frame',[[bpy.context.scene.frame_start]])    
        if 'End Frame' in self.outputs and self.outputs['End Frame'].links:
            SvSetSocketAnyType(self, 'End Frame',[[bpy.context.scene.frame_end]])
            
    def update_socket(self, context):
        self.update()


def register():
    bpy.utils.register_class(SvFrameInfoNode)
    
def unregister():
    bpy.utils.unregister_class(SvFrameInfoNode)

if __name__ == "__main__":
    register()
