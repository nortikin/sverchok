import bpy

def sv_back_to_parent(self, context):
    if context.space_data.tree_type == 'SverchCustomTreeType':
        layout = self.layout
        layout.operator("node.sv_tree_path_parent", icon='FILE_PARENT')


def register():
    bpy.types.NODE_HT_header.append(sv_back_to_parent)


def unregister():
    bpy.types.NODE_HT_header.remove(sv_back_to_parent)
