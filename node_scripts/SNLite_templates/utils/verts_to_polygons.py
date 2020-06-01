"""
in verts v
out faces s
"""

# this expects each incoming list of verts to represent a single polygon.
# this therefor expects incoming verts to be sequentially sorted already.

for vert_set in verts:
    faces.append([list(range(0, len(vert_set)))])
