
def make_contour(samples_x, samples_y, min_x, x_size, min_y, y_size, z, contour, make_faces=False, connect_bounds=False):
    n = len(contour)
    verts = []
    vert_0_bound = None
    vert_n_bound = None
    for i, (x0, y0) in enumerate(contour):

        if make_faces:
            if x0 <= 0:
                if i == 0:
                    vert_0_bound = 'A'
                elif i == n-1:
                    vert_n_bound = 'A'
            elif y0 <= 0:
                if i == 0:
                    vert_0_bound = 'D'
                elif i == n-1:
                    vert_n_bound = 'D'
            elif x0 >= samples_x-1:
                if i == 0:
                    vert_0_bound = 'C'
                elif i == n-1:
                    vert_n_bound = 'C'
            elif y0 >= samples_y-1:
                if i == 0:
                    vert_0_bound = 'B'
                elif i == n-1:
                    vert_n_bound = 'B'

        x = min_x + x_size * x0 + x_size/2.0
        y = min_y + y_size * y0 + y_size/2.0
        vertex = (x, y, z)
        verts.append(vertex)

    has_boundary = vert_0_bound is not None or vert_n_bound is not None
    is_inner = not has_boundary
    make_face = (is_inner or connect_bounds) and (make_faces and vert_0_bound == vert_n_bound)

    edges = [(i, i+1) for i in range(n-1)]
    if make_face:
        edges.append((n-1, 0))
    if make_face:
        face = list(range(n))
        faces = [face]
    else:
        faces = []
    return verts, edges, faces

def make_contours(samples_x, samples_y, min_x, x_size, min_y, y_size, z, contours, make_faces=False, connect_bounds=False):
    verts = []
    edges = []
    faces = []
    for contour in contours:
        new_verts, new_edges, new_faces = make_contour(samples_x, samples_y, min_x, x_size, min_y, y_size, z, contour, make_faces=make_faces, connect_bounds=connect_bounds)
        verts.append(new_verts)
        edges.append(new_edges)
        faces.append(new_faces)
    return verts, edges, faces

