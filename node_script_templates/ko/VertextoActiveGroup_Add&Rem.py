def sv_main(ObjectID=[], VertIND=[], Wei=[], remove=0):

    in_sockets = [
        ['v', 'ObjectID', ObjectID],
        ['s', 'Vert.INDEX', VertIND],
        ['s', 'Weight.(single)', Wei],
        ['s', 'Remove_if_1', remove]
        
        ]
    
    
    if ObjectID:
        if remove== 0:
            for i in ObjectID[0][0]:
                for i2 in VertIND[0]:
                    i.vertex_groups.active.add(i2, Wei[0][0][0], "REPLACE")
        else:
            for i in ObjectID[0][0]:
                for i2 in VertIND[0]:
                    i.vertex_groups.active.remove(i2)
    
    
    
    
    out_sockets = [
        ['v', 'void', [] ]
        
    ]
    
    return in_sockets, out_sockets