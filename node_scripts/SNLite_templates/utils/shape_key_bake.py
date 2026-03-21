"""
in  verts  v   .=[]    n=0
in  edges  s   .=[]    n=0
in  pols   s   .=[]    n=0
in frame   s   .=1     n=2
"""

import bpy
import bmesh
from mathutils import Vector


############  button part begins  ############

self.make_operator('make')

def ui(self, context, layout):
    cb_str = 'node.scriptlite_custom_callback'
    layout.operator(cb_str, text='B A K E').cb_name = 'make'


# main function
def make(self, context):
    import bpy
    import bmesh
    from mathutils import Vector
    # Remove extra brackets
    def okok(a):
        if a and len(a) > 0 and len(a[0]) > 0:
            return a[0]
        return []
    
    # Get input values
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

    # Validate inputs
    if not verts:
        print("No vertices to bake")
        return {'FINISHED'}

    # Find mesh or create
    mesh_name = 'sv_shape_key'
    obj_name = 'sv_shape_key'
    
    # Check if mesh exists
    if mesh_name in bpy.data.meshes:
        mesh = bpy.data.meshes[mesh_name]
        # Clear existing mesh data
        mesh.clear_geometry()
        mesh.from_pydata(verts, edges, pols)
        mesh.update()
    else:
        # Create new mesh
        mesh = bpy.data.meshes.new(name=mesh_name)
        mesh.from_pydata(verts, edges, pols)
        mesh.update()
    
    # Find object or create
    if obj_name in bpy.data.objects:
        obj = bpy.data.objects[obj_name]
        # Update mesh data
        obj.data = mesh
    else:
        obj = bpy.data.objects.new(obj_name, mesh)
    
    # Link object to collection (new way in 2.8+)
    if obj.name not in context.scene.collection.objects:
        context.scene.collection.objects.link(obj)
    
    # Make sure object is selected and active
    obj.select_set(True)
    context.view_layer.objects.active = obj
    
    # Shape keys adding
    # Make shape key basis first
    if not obj.data.shape_keys:
        basis = obj.shape_key_add(name='Basis')
        basis.value = 0.0
    
    # Create new shape key with frame number
    sk_name = f"sverchok {frame}"
    
    # Get or create shape key
    shape_keys = obj.data.shape_keys
    
    # Check if shape key already exists
    if shape_keys and sk_name not in shape_keys.key_blocks:
        # Add new shape key
        sk = obj.shape_key_add(name=sk_name)
        
        # Check for equal length of vertices
        if len(obj.data.vertices) != len(verts):
            print(f"Vertex count mismatch: object has {len(obj.data.vertices)}, input has {len(verts)}")
            return {'FINISHED'}
        
        # Set shape key to relative mode (Absolute mode)
        shape_keys.use_relative = False
        
        # Update vertex positions for the new shape key
        for i, v in enumerate(verts):
            if i < len(sk.data):
                sk.data[i].co = Vector(v)
        
        print(f"Created shape key '{sk_name}' with {len(verts)} vertices")
    else:
        print(f"Shape key '{sk_name}' already exists")
    
    ############  button part return finished  ############
    return {'FINISHED'}