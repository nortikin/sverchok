def sv_main(ObjectID=[], rotation_euler=[], scale=[], location=[]):

    in_sockets = [
        ['v', 'Object(ID)', ObjectID],
        ['v', 'Rotation_euler', rotation_euler],
        ['v', 'Scale', scale],
        ['v', 'Location', location]
        
        ]
    
    import mathutils 
    from mathutils import Vector
    
    
    
    
    if ObjectID:
        for i in ObjectID[0]:
            for i2 in i:
                if rotation_euler:
                    i2.rotation_euler= Vector(rotation_euler[0][0])
                if scale:
                    i2.scale= Vector(scale[0][0])
                if location:
                    i2.location= Vector(location[0][0])    
    
    
    out_sockets = [
        ['v', 'void', [] ]
    ]
 
    return in_sockets, out_sockets