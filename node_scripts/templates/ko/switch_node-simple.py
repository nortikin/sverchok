def sv_main(n1=1, num1=[[]], num2=[[]]):

    in_sockets = [
        ['s', 'Condition_(single)',  n1],       # Formula2 expression such as X>4 or (X>4)&(X<n[2]).
        ['s', 'Num_if_True',  num1],
        ['s', 'Num_if_False',  num2],
    ]

    
    
    if n1: 
        outn=num1
    else:
        outn=num2
    
    

    out_sockets = [
        ['s', 'NumbersWin', outn],
    ]

    return in_sockets, out_sockets

# This node can be useful for animation purposes.
