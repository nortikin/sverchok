"""
in  verts  v   .=[]    n=0
in  edges  s   .=[]    n=0
in  pols   s   .=[]    n=0
in frame   s   .=1     n=2
"""

import bpy
import bmesh


############  button part begins  ############

self.make_operator('make')

def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='B A K E').cb_name='make'


# main function
def make(self, context):
    from mathutils import Vector
    #for remove extra brecket
    def okok(a):
        if a:
            return a[0]
        else:
            return []
    frame = self.inputs['frame'].sv_get()[0][0]
    verts = okok(self.inputs['verts'].sv_get())
    if self.inputs['pols'].is_linked:
        pols = okok(self.inputs['pols'].sv_get())
    else:
        pols = []
    if self.inputs['edges'].is_linked:
        edges = okok(self.inputs['edges'].sv_get())
    else:
        edges = []

    ############  button part ends  ############

    # find mesh or create
    if not 'sv_shape_key' in bpy.data.meshes:
        mesh = bpy.data.meshes.new(name='sv_shape_key')
        mesh.from_pydata(verts,edges,pols)
    else:
        mesh = bpy.data.meshes['sv_shape_key']
    # find object or create
    if not 'sv_shape_key' in bpy.data.objects:
        obj = bpy.data.objects.new("sv_shape_key", mesh)
        bpy.context.scene.objects.link(obj)
    else:
        obj = bpy.data.objects['sv_shape_key']
    if not 'sv_shape_key' in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(obj)


    # shapekeys adding
    # make shape key basis at first
    if not obj.data.shape_keys:
        sk0 = obj.shape_key_add(name='Basis')
    else:
        # name of new shape from frame number
        kn = f"sverchok {frame}"
    key = bpy.data.shape_keys[obj.data.shape_keys.name]
    key.use_relative = False


    # check for equal length of vertices
    if len(obj.data.vertices) != len(verts):
        return
    # current frame to add
    if kn not in key.key_blocks:
        sk = obj.shape_key_add(name=kn)
        for i,v in enumerate(verts):
            key.key_blocks[kn].data[i].co = Vector(v)
    ############  button part return finished  ############
    return {'FINISHED'}

#bpy.data.shape_keys[obj.data.shape_keys.name].key_blocks[kn].data[:].co