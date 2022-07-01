"""
in verts v
"""

def my_operator(self, context):
    print(self, context, self.inputs['verts'].sv_get())
    return {'FINISHED'}

self.make_operator('my_operator')
 
def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='show me').cb_name='my_operator'
