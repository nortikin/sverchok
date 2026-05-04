"""
out stuff     s
"""

def ui(self, context, layout):
    scn = context.scene
    if not hasattr(scn, 'some_scriptnode_prop'):
        return
    layout.prop(scn, 'some_scriptnode_prop')
        
scn = bpy.context.scene
if hasattr(scn, 'some_scriptnode_prop'):
    print(scn.some_scriptnode_prop)
    stuff = [[scn.some_scriptnode_prop]]
else:
    bpy.types.Scene.some_scriptnode_prop = bpy.props.StringProperty()