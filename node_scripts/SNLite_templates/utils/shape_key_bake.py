"""
in  verts  v   .=[]    n=0
in  edges  s   .=[]    n=0
in  pols   s   .=[]    n=0
in active  s   .=0     n=2
in frame   s   .=1     n=2
"""

import bpy
import bmesh
from mathutils import Vector


#for remove extra brecket
def okok(a):
    if a:
        return a[0]
    else:
        return []
verts = okok(verts)
edges = okok(edges)
pols = okok(pols)

# main function
def make():
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
        kn = "sverchok %d"%frame
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

if active and verts:
    make()
#bpy.data.shape_keys[obj.data.shape_keys.name].key_blocks[kn].data[:].co