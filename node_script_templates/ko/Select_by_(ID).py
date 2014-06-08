def sv_main(pt_1=[], con=0):
 
    
    in_sockets = [
        ['v', 'Object(ID)',  pt_1],
        ['s', 'Sel/Desel_if_1/0',  con]
    ]
    
    
    n=[]
    if pt_1:
        for i in pt_1[0]:
            for i2 in i:
                i2.select= con
        
    
    
    out_sockets = [
        ['v', 'void', [] ]
    ]
 
    return in_sockets, out_sockets