import bpy
from sverchok.utils.sv_monad_tools import SvTreePathParent

def sv_back_to_parent(self, context):
    op_poll = SvTreePathParent.poll
    if op_poll(context):
        layout = self.layout
        layout.operator("node.sv_tree_path_parent", text='sv parent', icon='FILE_PARENT')


def register():
    bpy.types.NODE_HT_header.prepend(sv_back_to_parent)


def unregister():
    bpy.types.NODE_HT_header.remove(sv_back_to_parent)
