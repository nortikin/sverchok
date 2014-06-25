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
    
    objL=[]
    objN=[]
    objI=[]
    
    
    if Vec1 and Vec2:
        start= [Vector(x) for x in Vec1[0]]
        end= [Vector(x) for x in Vec2[0]]

    if ObjectID:
        objects= ObjectID[0][0]
    else:
        objects= bpy.context.selected_objects    
    
    for i in objects:
            for i2 in [i.ray_cast(a,b) for a in start for b in end]:
        
                objL.append( i2[0][:] )    
                objN.append( i2[1][:] )
                objI.append( i2[2] )
        
    
    out_sockets = [
        ['v', '(obj.)HitLocation', [objL] ],
        ['v', '(obj.)HitNormal', [objN] ],
        ['s', '(obj.)FaceIndex', [objI] ]
    ]
 
    return in_sockets, out_sockets