def sv_main(N1=[], N2=[], M=[]):

    in_sockets = [
        ['s', 'N1', N1],
        ['s', 'N2', N2],
        ['s', 'M', M]]
    
    
    out=[]
    
    g=0
    while g< len( M ):
        
        for i in M[0][g]:
            if i== 0:
                out.append( N1[0][g] )
            else:
                out.append( N2[0][g] )    
            g= g+1
    
    
    out_sockets = [
        ['v', 'Location', [out] ]
    ]
    
    return in_sockets, out_sockets