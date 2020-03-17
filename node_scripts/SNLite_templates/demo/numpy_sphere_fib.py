"""
in samples s d=400 n=2
in rseed s d=4 n=2
in mult s d=1.0 n=2
out verts_out v
"""
import numpy as np
import math, random

def fibonacci_sphere_np(samples, rseed):
    indices = np.arange(samples)    
    rnd = 1.
    random.seed(rseed)
    rnd = random.random() * samples
    offset = 2./samples
    increment = math.pi * (3. - math.sqrt(5.))

    y = ((indices * offset) - 1) + (offset / 2)
    r = np.sqrt(1 - pow(y, 2))
    phi = ((indices + rnd) % samples) * increment    
    x = np.cos(phi) * r
    z = np.sin(phi) * r
    return (np.vstack([x,y,z])*mult).T.tolist()
    
p = fibonacci_sphere_np(samples, rseed)
verts_out.extend([p])
