import bpy
from node_s import *
from util import *

class VertsDelDoublesNode(Node, SverchCustomTreeNode):
    ''' Delete doubles vertices '''
    bl_idname = 'VertsDelDoublesNode'
    bl_label = 'Delete Double vertices'
    bl_icon = 'OUTLINER_OB_EMPTY'
    
    def draw_buttons(self, context, layout):
        # if to make button - use name of socket and name of tree
        # will be here soon
        pass
        
    def init(self, context):
        self.inputs.new('VerticesSocket', "vers", "vers")
        self.outputs.new('VerticesSocket', "vers", "vers")
        
    def update(self):
        
        if 'vers' in self.outputs and len(self.outputs['vers'].links)>0:
            # get any type socket from input:
            vers = SvGetSocketAnyType(self, self.inputs['vers'])
            # Process data
            levs = levelsOflist(vers)
            result = self.remdou(vers, levs)
            SvSetSocketAnyType(self, 'vers', result)
            
    def remdou(self, vers, levs):
        out = []
        if levs >= 3:
            levs -= 1
            for x in vers:
                out.append(self.remdou(x,levs))
        else:
            for x in vers:
                if x not in out:
                    out.append(x)
        return out


def register():
    bpy.utils.register_class(VertsDelDoublesNode)
    
def unregister():
    bpy.utils.unregister_class(VertsDelDoublesNode)


if __name__ == "__main__":
    register()
