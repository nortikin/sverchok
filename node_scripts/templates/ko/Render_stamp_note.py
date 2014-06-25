def sv_main(st=[]):

    in_sockets = [
        ['s', 'Formula2:"txt"+str(x)', st]]    
    
    if st:
        
        bpy.context.scene.use_stamp_note= str(st[0][0][0])   # check it on Properties->Render->Stamp.
    
    
  
    out_sockets = [
        ['v', 'Void', []]   # Empty. Becose there must be at least one.
    ]
 
    return in_sockets, out_sockets