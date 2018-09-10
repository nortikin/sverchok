"""
in bounds s d=10 n=2
in iso_val s d=8.0 n=2
in samples s d=100 n=2
out vertices v
out triangles s
"""


import numpy as np
import sys
import math
import os
try:
    mcubes_path = r"/usr/local/lib/python3.5/dist-packages" #it depend on your OS but just paste the path where is mcubes
    if not mcubes_path in sys.path:
        sys.path.append(mcubes_path)    
    import mcubes
except:
    os.system('pip3 install pymcubes')
# Create the volume
def f(x, y, z):
    return (z**3 / (math.sin(z*y+x)) + 3**x)**3

# Create a data volume (30 x 30 x 30)
#X, Y, Z = np.mgrid[:100, :100, :100]
# u = (X-50)**2 + (Y-50)**2 + (Z-50)**2 - 25**2

# Extract the 0-isosurface
#verts, tri = mcubes.marching_cubes(u, 0)

# Extract the 16-isosurface
verts, tri = mcubes.marching_cubes_func(
        (-bounds, -bounds, -bounds), (bounds, bounds, bounds),  # Bounds
        samples, samples, samples,              # Number of samples in each dimension
        f,                          # Implicit function
        iso_val)                         # Isosurface value

vertices, triangles = verts.tolist(), tri.tolist()