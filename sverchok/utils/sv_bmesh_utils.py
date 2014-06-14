import bmesh

def bmesh_from_pydata(verts=[], edges=[], faces=[]):
    ''' verts is necessary, edges/faces are optional '''

    bm = bmesh.new()
    add_vert = bm.verts.new
    [add_vert(co) for co in verts]
    bm.verts.index_update()

    if faces:
        add_face = bm.faces.new
        for face in faces:
            add_face(tuple(bm.verts[i] for i in face))
        bm.faces.index_update()

    if edges:
        add_edge = bm.edges.new
        for edge in edges:
            edge_seq = tuple(bm.verts[i] for i in edge)
            try:
                add_edge(edge_seq)
            except ValueError:
                # edge exists!
                pass

        bm.edges.index_update()

    return bm
