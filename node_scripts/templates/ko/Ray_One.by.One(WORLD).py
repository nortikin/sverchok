def sv_main(Vec1=[], Vec2=[]):

    in_sockets = [
        ['v', 'Start', Vec1],
        ['v', 'End', Vec2]
        
        ]
    
    import mathutils 
    from mathutils import Vector


    start=[]
    end=[]
    outLoc=[]
    OutNorm=[]
    ObjID=[]
    Matrix=[]
    HittSucces=[]

    if Vec1 and Vec2:
        start= [Vector(x) for x in Vec1[0]]
        end= [Vector(x) for x in Vec2[0]]

        i=0
        while i< len(end):
            
            outLoc.append(bpy.context.scene.ray_cast(start[i],end[i])[3][:])
            OutNorm.append(bpy.context.scene.ray_cast(start[i],end[i])[4][:])
            ObjID.append(bpy.context.scene.ray_cast(start[i],end[i])[1])
            HittSucces.append(bpy.context.scene.ray_cast(start[i],end[i])[0])
            
            Matrix.append(bpy.context.scene.ray_cast(start[i],end[i])[2][:])
            Matrix= [ [a[:],b[:],c[:],d[:]] for a,b,c,d in Matrix ]

            
            i= i+1
    
    
    
    out_sockets = [
        ['v', 'Hit_Location', [outLoc] ],
        ['v', 'Normal', [OutNorm] ],
        ['v', 'BPY_Object', [ObjID] ],
        ['v', 'HittSucces', [HittSucces] ],
        ['m', 'Matrix', Matrix ]
    ]
 
    return in_sockets, out_sockets