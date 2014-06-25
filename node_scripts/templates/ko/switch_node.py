def sv_main(n1=1, vec1=[], num1=[], mat1=[], vec2=[], num2=[], mat2=[], invert=0):

    in_sockets = [
        ['s', 'Condition_(single)',  n1],       # Formula2 expression such as X>4 or (X>4)&(X<n[2]).
        ['v', 'Vec_if_True',  vec1],
        ['s', 'Num_if_True',  num1],
        ['m', 'Mat_if_True',  mat1],
        ['v', 'Vec_if_False',  vec2],
        ['s', 'Num_if_False',  num2],
        ['m', 'Mat_if_False',  mat2],
        ['s', 'Invert_if_1_(single)',  invert]       # Can be anoter expression. In Python True/False == 1/0 and vise versa.
    ]

    
    if invert==1:
        true=0
    else:
        true=1   
    
    if n1==true: 
        outv=vec1
        outn=num1
        outm=mat1
        outvl=vec2
        outnl=num2
        outml=mat2
    else:
        outv=vec2
        outn=num2
        outm=mat2
        outvl=vec1
        outnl=num1
        outml=mat1    
    
    

    out_sockets = [
        
        ['v', 'VectorsWin', outv],
        ['s', 'NumbersWin', outn],
        ['m', 'MatrixWin', outm],
        ['v', 'VectorsLoose', outvl],
        ['s', 'NumbersLoose', outnl],
        ['m', 'MatrixLoose', outml],
        ['s', 'Is_Inverted', [invert]]
    ]

    return in_sockets, out_sockets

# This node can be useful for animation purposes.