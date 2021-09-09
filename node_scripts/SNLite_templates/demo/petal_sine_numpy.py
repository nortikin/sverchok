"""
in   n_petals s        default=8       nested=2
in   vp_petal s        default=10      nested=2
in   profile_radius s  ;=2.3           n=2
in   amp s             default=1.0     nested=2
in   origin v          defautt=(0,0,0) n=2
out  verts v
out  edges s
"""
from sverchok.data_structure import get_edge_loop

TAU = np.pi * 2
N = n_petals * vp_petal

pi_vals = np.tile(np.linspace(0, TAU, int(vp_petal), endpoint=False), n_petals)
amps = np.cos(pi_vals) * amp
theta = np.linspace(0, TAU, int(N), endpoint=False)
circle_coords = np.array([np.sin(theta), np.cos(theta), np.zeros(N)])
coords = circle_coords.T * (profile_radius + amps.reshape((-1, 1)))

# apply origin location translation
coords += np.array(origin)
verts.append(coords.tolist())

# use optimized edge loop function (cyclic.. )
final_edges = get_edge_loop(N)
edges.append(final_edges)
