from numba import njit

@njit
def get_average_vector(verts, n):
    dummy_vec = Vector()
    for v in verts:
        dummy_vec = dummy_vec + v
    return dummy_vec * 1/n

@njit
def do_tri(face, lv_idx, make_inner):
    a, b, c = face
    d, e, f = lv_idx-2, lv_idx-1, lv_idx
    out_faces = []
    out_faces.append([a, b, e, d])
    out_faces.append([b, c, f, e])
    out_faces.append([c, a, d, f])
    if make_inner:
        out_faces.append([d, e, f])
        new_insets.append([d, e, f])
    return out_faces

@njit
def do_quad(face, lv_idx, make_inner):
    a, b, c, d = face
    e, f, g, h = lv_idx-3, lv_idx-2, lv_idx-1, lv_idx
    out_faces = []
    out_faces.append([a, b, f, e])
    out_faces.append([b, c, g, f])
    out_faces.append([c, d, h, g])
    out_faces.append([d, a, e, h])
    if make_inner:
        out_faces.append([e, f, g, h])
        new_insets.append([e, f, g, h])
    return out_faces

@njit
def do_ngon(face, lv_idx, make_inner):
    '''
    setting up the forloop only makes sense for ngons
    '''
    num_elements = len(face)
    face_elements = list(face)
    inner_elements = [lv_idx-n for n in range(num_elements-1, -1, -1)]
    # padding, wrap-around
    face_elements.append(face_elements[0])
    inner_elements.append(inner_elements[0])

    out_faces = []
    add_face = out_faces.append
    for j in range(num_elements):
        add_face([face_elements[j], face_elements[j+1], inner_elements[j+1], inner_elements[j]])

    if make_inner:
        temp_face = [idx[-1] for idx in out_faces]
        add_face(temp_face)
        new_insets.append(temp_face)

    return out_faces



def inset_special(vertices, faces, inset_rates, distances, ignores, make_inners, zero_mode="SKIP"):

    new_faces = []
    new_ignores = []
    new_insets = []

    def new_inner_from(face, inset_by, distance, make_inner):
        '''
        face:       (idx list) face to work on
        inset_by:   (scalar) amount to open the face
        axis:       (vector) axis relative to face normal
        distance:   (scalar) push new verts on axis by this amount
        make_inner: create extra internal face

        # dumb implementation first. should only loop over the verts of face 1 time
        to get
         - new faces
         - avg vertex location
         - but can't lerp until avg is known. so each input face is looped at least twice.
        '''
        current_verts_idx = len(vertices)
        n = len(face)
        verts = [vertices[i] for i in face]
        avg_vec = get_average_vector(verts, n)

        if abs(inset_by) < 1e-6:
            normal = mathutils.geometry.normal(*verts)
            new_vertex = avg_vec.lerp(avg_vec + normal, distance)
            vertices.append(new_vertex)
            new_vertex_idx = current_verts_idx
            new_faces
            for i, j in zip(face, face[1:]):
                new_faces.append([i, j, new_vertex_idx])
            new_faces.append([face[-1], face[0], new_vertex_idx])
            return

        # lerp and add to vertices immediately
        new_verts_prime = [avg_vec.lerp(v, inset_by) for v in verts]

        if distance:
            local_normal = mathutils.geometry.normal(*new_verts_prime)
            new_verts_prime = [v.lerp(v+local_normal, distance) for v in new_verts_prime]

        vertices.extend(new_verts_prime)

        tail_idx = (current_verts_idx + n) - 1

        get_faces_prime = {3: do_tri, 4: do_quad}.get(n, do_ngon)
        new_faces_prime = get_faces_prime(face, tail_idx, make_inner)
        new_faces.extend(new_faces_prime)

    for idx, face in enumerate(faces):
        inset_by = inset_rates[idx]

        good_inset = (inset_by > 0) or (zero_mode == 'FAN')
        if good_inset and (not ignores[idx]):
            new_inner_from(face, inset_by, distances[idx], make_inners[idx])
        else:
            new_faces.append(face)
            new_ignores.append(face)

    new_verts = [v[:] for v in vertices]
    return new_verts, new_faces, new_ignores, new_insets
