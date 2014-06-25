def sv_main(Name=[]):

    in_sockets = [
        ['v', 'Image_Name', Name]
        
        ]
    
    import mathutils 
    from mathutils import Vector
    
    size=[]
    pixels=[]
    
    def chunks(l, n):
            if n<1:
                n=1
            return [l[i:i+n] for i in range(0, len(l), n)]
    
    
    
    
    if Name:
        
        size.append(bpy.data.images.get(Name[0][0][0]).size[:2])
        
        pixels.append( bpy.data.images.get(Name[0][0][0]).pixels[:] )
        pixels= chunks(pixels[0], 4) 

    
    
    
    
    
    out_sockets = [
        ['v', 'Size', [size] ],
        ['s', 'pixels', [pixels] ]
    ]
 
    return in_sockets, out_sockets