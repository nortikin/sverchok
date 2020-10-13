'''
in data s d=[[]] n=0
in mask s d=[[]] n=0
in level s d=2 n=2
out data_out s
'''

from sverchok.nodes.list_struct.flip import flip


def rec(data_in, mask, level):
    # рекурсия маскировки
    print(level)
    if level > 1:
        l = level - 1
        dic = []
        for d,m in zip(data_in,mask):
            dic.append(rec(d,m,l))
        return dic
    else:
        data_out = []
        dic = {}
        for d,m in zip(data_in,mask):
            if not m in dic: 
                dic[m] = []
            dic[m].append(d)
        for v in dic.values():
            data_out.append(v)
        return data_out

data_out = flip(rec(data,mask,level),level-2)