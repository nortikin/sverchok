
"""
in pols_in s d=[[]] n=0
out pols_out s
"""

ou = []
v1 = pols_in[0]
#print(v1[:10])
flag_joined = False
for i in range(len(v1)):
    p = v1[i]
    if i == 0:
        ou.append(p)
        #print('first')
        continue
    #tf1 = [i in v1[i-1] for i in v1[i]]
    if v1[i][2] == v1[i-1][1] and v1[i][3] == v1[i-1][0] and flag_joined == False:
        #i11, i12 = tf1.index(False,0), tf1.index(False,-1)
        #i13, i14 = tf1.index(True,0), tf1.index(True,-1)
        #tf2 = [i in v1[i] for i in v1[i-1]]
        #print('truefalses',tf1, tf2, v1[i],v1[i-1])
        #i21, i22 = tf2.index(True,0), tf2.index(True,-1)
        if flag_joined == False:
            ou.pop(-1)
        p = [ v1[i][0], v1[i][1], v1[i-1][2], v1[i-1][3] ]
        flag_joined = True
        ou.append(p)
        #plan = v1[i].extend(v1[i-1])
        #p = list(set(plan))
    elif flag_joined == True:
        flag_joined = False
        ou.append(p)
    else:
        ou.append(p)
pols_out.append(ou)