def sv_main(Vec1=[], Vec2=[], ObjectID=[]):

    in_sockets = [
        ['v', 'Start', Vec1],
        ['v', 'End', Vec2],
        ['v', 'Object(ID)', ObjectID]
        
        ]
    
    import mathutils 
    from mathutils import Vector


    start=[]
    end=[]
    OutLoc=[]
    OutNorm=[]
    FaceINDEX=[]
    
    if Vec1 and Vec2:
        start= [Vector(x) for x in Vec1[0]]
        end= [Vector(x) for x in Vec2[0]]

    if ObjectID:
        objects= ObjectID[0][0]
    else:
        objects= bpy.context.selected_objects    
    
    
    
    out=[]
    for i in objects:
        i2=0
        while i2< len(end):
            out.append(i.ray_cast(start[i2],end[i2]))
            i2= i2+1
    
    
    for i in out:
        OutLoc.append(i[0][:])
        OutNorm.append(i[1][:])
        FaceINDEX.append(i[2])
    
    
    

    out_sockets = [
        ['v', 'Hit_Location', [OutLoc] ],
        ['v', 'Normal', [OutNorm] ],
        ['s', 'FaceINDEX', [FaceINDEX] ]
    ]
 
    return in_sockets, out_sockets