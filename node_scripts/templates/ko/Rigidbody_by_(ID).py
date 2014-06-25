def sv_main(pt_1=[], con1=1, con2=0, mass=1.0, friction=0.5):
 
    
    in_sockets = [
        ['v', 'Object(ID)',  pt_1],
        ['s', 'Enable/Disable_if_1/0',  con1],
        ['s', 'Kinematic/Not_if_1/0',  con2],
        ['s', 'Mass',  mass],
        ['s', 'Friction',  friction]
    ]
    
    
    n=[]
    if pt_1:
        for i in pt_1[0]:
            for i2 in i:
#------------------------------------------------------------------                
                if con1==0:
                    i2.rigid_body.enabled= 0
                else:
                    i2.rigid_body.enabled= 1    
#------------------------------------------------------------------                
                if con2==0:
                    i2.rigid_body.kinematic= 0
                else:
                    i2.rigid_body.kinematic= 1    
#------------------------------------------------------------------                
                if mass:
                    i2.rigid_body.mass= mass
                
                if friction:
                    i2.rigid_body.friction= friction            
        
    
    
    out_sockets = [
        ['v', 'void', [] ]
    ]
 
    return in_sockets, out_sockets