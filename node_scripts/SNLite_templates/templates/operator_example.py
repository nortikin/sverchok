"""
in verts v
"""

def my_operator(self, context):
    # this will have a limited knowledge of the globally available variables
    # the aliases will be available. ( see self.snlite_aliases.keys())
    print(self, context, self.inputs['verts'].sv_get())
    return {'FINISHED'}

self.make_operator('my_operator')
 
def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='show me').cb_name='my_operator'
