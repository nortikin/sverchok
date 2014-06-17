def sv_main(newloc=[]):

    in_sockets = [
        ['v', 'newlocx', newloc]
     ]
    if newloc:
        bpy.context.scene.cursor_location = (newloc[0][0])
    
    Vout= [bpy.context.scene.cursor_location[:]]
    out_sockets = [
        ['v', 'Cursor Location', [Vout]]
    ]

    return in_sockets, out_sockets