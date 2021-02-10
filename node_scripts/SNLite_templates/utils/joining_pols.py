
"""
in pols_in s d=[[]] n=0
out pols_out s
"""
## This script will join quad polygons by pairs
## if the third and fourth indices of that polygon are equal to
## the second and the first indices of the next polygon, 
## is ready to work with the Plane Node

for pols in pols_in:
    ou = []
    v1 = pols

    flag_joined = False
    for i in range(len(v1)):
        p = v1[i]
        if i == 0:
            ou.append(p)
            continue

        if v1[i][2] == v1[i-1][1] and v1[i][3] == v1[i-1][0] and flag_joined == False:
            if flag_joined == False:
                ou.pop(-1)
            p = [ v1[i][0], v1[i][1], v1[i-1][2], v1[i-1][3] ]
            flag_joined = True
            ou.append(p)

        elif flag_joined == True:
            flag_joined = False
            ou.append(p)
        else:
            ou.append(p)
    pols_out.append(ou)
