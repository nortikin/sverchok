"""
in num_points s d=100 n=2
in dist_cen s d=22 n=2
in scale_factor s d=0.13 n=2
out verts v
"""
import numpy as np
from math import radians

i = np.arange(dist_cen, num_points)
theta = i * radians(137.5)
r = np.sqrt(i) * scale_factor
X = np.cos(theta) * r 
Y = np.sin(theta) * r
Z = np.zeros(i.size)
fverts = np.vstack([X, Y, Z]).T.tolist()

verts.append(fverts)
