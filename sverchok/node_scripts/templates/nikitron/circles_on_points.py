# not finished yet
# will create circles field in what circles will fill maximum space

from math import sin, cos, radians, pi, sqrt
from mathutils import Vector, Euler
from random import random


def sv_main(v=[],c=3):

    in_sockets = [
        ['v', 'vertices',  v],
        ['s', 'circle',  c],
    ]

    if v:
        max_ = max([i[0] for i in v])
        mix_ = min([i[0] for i in v])
        may_ = max([i[1] for i in v])
        miy_ = min([i[1] for i in v])
        area = (max_-mix_)*(may_-miy_)
        radiuses = [0.2]
        points = [[0,0,0]]
        badpoints=[]
        for i in range(10):
            newarea = area * pow(i, 1/c)
            rad = sqrt(newarea/pi)
            t=True
            print("defined radius", rad)
            while t:
                randx=random()*(max_-mix_)
                randy=random()*(may_-miy_)
                for u, p in enumerate(points):
                    if (p[0] - randx)**2 + (p[1] - randy)**2 < (radiuses[u]**2)+rad:
                        t=False
                    else:
                        print('bad point')
                        badpoints.append([randx+mix_,randy+miy_,0])
                #print('check circles', rad)
            radiuses.append(rad)
            points.append([randx+mix_,randy+miy_,0])
            print('one circle', str([randx+mix_,randy+miy_,0]))
    else:
        points=[]
        radiuses=[]
        badpoints=[]
    out_sockets = [
        ['v', 'centers', [points]],
        ['s', 'radiuses', [radiuses]],
        ['v', 'bads', [badpoints]],
    ]

    return in_sockets, out_sockets
