def sv_main(Vec1=[], Vec2=[]):

    in_sockets = [
        ['v', 'Start', Vec1],
        ['v', 'End', Vec2]
        
        ]
    
    import mathutils 
    from mathutils import Vector
    
    
    
    HittSucces=[]
    start=[]
    end=[]
    HitPoints=[]
    HittNormals=[]
    Matrix=[]
    Name=[]
    
    
    
    if Vec1 and Vec2:
        start= [Vector(x) for x in Vec1[0]]
        end= [Vector(x) for x in Vec2[0]]
    
    for i in [bpy.context.scene.ray_cast(a,b) for a in start for b in end]:
        
        HittSucces.append( i[0] )
        HitPoints.append( i[3][:] )
        HittNormals.append( i[4][:] )
        
        Matrix.append( i[2][:] )
        Matrix= [ [a[:],b[:],c[:],d[:]] for a,b,c,d in Matrix  ]
        
        Name.append( i[1] )  # <bpy_struct, Object("_")>
    
        
        
    
    out_sockets = [
        ['v', 'HitPoints', [HitPoints] ],
        ['v', 'HittNormals', [HittNormals] ],
        ['v', 'HittSucces', [HittSucces] ],
        ['m', 'Matrix', Matrix ],
        ['v', 'Object(ID)', [Name] ],
        
     ]
 
    return in_sockets, out_sockets