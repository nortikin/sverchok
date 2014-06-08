def sv_main(Grav_Normal=[]):

    in_sockets = [
        ['v', 'Grav_Normal', Grav_Normal]]    
    
    
    
    bpy.context.scene.use_gravity= 1
    
    if Grav_Normal:
        bpy.context.scene.gravity = (Grav_Normal[0][0])
        
    Grav_Normal= [bpy.context.scene.gravity[:]]
    out_sockets = [
        ['v', 'Grav_Normal_out', [Grav_Normal]]
    ]
    return in_sockets, out_sockets


# Starting to affect rigid-body simulation then placed in node-tree.