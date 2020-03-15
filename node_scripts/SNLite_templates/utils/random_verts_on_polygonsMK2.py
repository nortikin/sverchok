"""
in verts_list v
in faces_list s
in num_points s d=20 n=2
out verts_out v
"""

import bpy_extras
import mathutils
from mathutils import Vector
from bpy_extras import mesh_utils

for verts, faces in zip(verts_list, faces_list):

    mesh = []
    tessellated_faces = []
    add_face = tessellated_faces.append

    try:
        for f in faces:
            if len(f) in {3, 4}:
                add_face(f)
            else:
                # Takes a list of polylines (each point a vector) and returns the point indices for a polyline filled with triangles.
                v = [Vector(verts[i]) for i in f]
                tess_poly = mathutils.geometry.tessellate_polygon([v])
                for tess in tess_poly:
                    add_face([f[i] for i in tess])

        mesh = bpy.data.meshes.new(name="xxxxaaaa")
        mesh.from_pydata(verts, [], tessellated_faces)

        tessfaces = mesh.polygons
        new_verts = mesh_utils.triangle_random_points(num_points, tessfaces)
        verts_out.append([v[:] for v in new_verts])
        
        if "xxxxaaaa" in bpy.data.meshes:
            bpy.data.meshes.remove(mesh)

    except Exception as err:
        print('nope', err)




def face_random_points_ngons(num_points, tessfaces):

    from random import random
    import mathutils
    from mathutils.geometry import area_tri, tessellate_polygon

    # Split all quads into 2 tris, tris remain unchanged
    tri_faces = []
    for f in tessfaces:
        tris = []
        verts = f.id_data.vertices
        fv = f.vertices[:]

        if len(fv) == 3:
            tris.append((verts[fv[0]].co, verts[fv[1]].co, verts[fv[2]].co))
        elif len(fv) == 4:
            tris.append((verts[fv[0]].co, verts[fv[1]].co, verts[fv[2]].co))
            tris.append((verts[fv[0]].co, verts[fv[3]].co, verts[fv[2]].co))
        else:
            fvngon = [v.co for v in verts]
            tris.extend([[fvngon[i] for i in tess] for tess in tessellate_polygon([fvngon])])

        tri_faces.append(tris)

    # For each face, generate the required number of random points
    sampled_points = [None] * (num_points * len(tessfaces))
    # sampled points need to be vectorized as npo below
    for i, tf, npo in enumerate(zip(tri_faces,num_points)):
        for k in range(npo):
            # If this is a quad, we need to weight its 2 tris by their area
            if len(tf) == 2:

                area1 = area_tri(*tf[0])
                area2 = area_tri(*tf[1])
                area_tot = area1 + area2
                area1 = area1 / area_tot
                area2 = area2 / area_tot
                vecs = tf[0 if (random() < area1) else 1]

            elif len(tf) == 1:

                vecs = tf[0]

            else:

                areas = [area_tri(*tface) for tface in tf]
                area_tot = sum(areas)
                areas = [(area / area_tot) for area in areas]

                #  vecs = tf[0 if (random() < area1) else 1]   ???

            u1 = random()
            u2 = random()
            u_tot = u1 + u2

            if u_tot > 1:
                u1 = 1.0 - u1
                u2 = 1.0 - u2

            side1 = vecs[1] - vecs[0]
            side2 = vecs[2] - vecs[0]

            p = vecs[0] + u1 * side1 + u2 * side2

            sampled_points[npo * i + k] = p

    return sampled_points
