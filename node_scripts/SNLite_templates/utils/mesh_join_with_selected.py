'''
in vers v
in pols s
in vdata s
in pdata s
out vers_out v
out pols_out s
out vdata_out s
out pdata_out s
'''

for v,w,u,y in zip(vers,pols,vdata,pdata):
    v_,p_,s_,d_ = [],[],[],[]
    for pol,dat in zip(w,y):
        v_.append([list(v[i]) for i in pol])
        p_.append([[i for i, k in enumerate(pol)]])
        s_.append([u[i] for i in pol])
        d_.append([dat])
    vers_out.extend(v_)
    pols_out.extend(p_)
    vdata_out.extend(s_)
    pdata_out.extend(d_)
