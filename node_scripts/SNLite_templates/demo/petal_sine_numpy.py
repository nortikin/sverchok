"""
in   n_petals s        default=8       nested=2
in   vp_petal s        default=10      nested=2
in   profile_radius s  ;=2.3           n=2
in   amp s             default=1.0     nested=2
in   origin v          defautt=(0,0,0) n=2
out  verts v
out  edges s
"""

TAU = np.pi * 2
N = n_petals * vp_petal

pi_vals = np.linspace(0, TAU, vp_petal, endpoint=False)
pi_vals = np.tile(pi_vals, n_petals)
amps = np.cos(pi_vals) * amp
unit_circle = np.linspace(0, TAU, N, endpoint=False)
circle_coords = np.array([np.sin(unit_circle), np.cos(unit_circle), np.zeros(N)])
coords = circle_coords.T* (profile_radius + amps.reshape((-1, 1)))
verts.append(coords.tolist())

edge_indices_a = np.arange(0, N)
edge_indices_b = np.roll(edge_indices_a, -1)
final_edges = np.array([edge_indices_a, edge_indices_b]).T.tolist()
edges.append(final_edges)
