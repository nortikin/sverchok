def sv_main(size=1.0, divx=1, divy=1, divz=1):

    in_sockets = [
        ['s', 'size', size],
        ['s', 'divx', divx],
        ['s', 'divy', divy],
        ['s', 'divz', divz]
    ]

    def gen_cube():

        if 0 in (divx, divy, divz):
            return [], []

        b = size / 2.0

        verts = [
            [b, b, -b], [b, -b, -b], [-b, -b, -b],
            [-b, b, -b], [b, b, b], [b, -b, b],
            [-b, -b, b], [-b, b, b]
        ]

        faces = [[0, 1, 2, 3], [4, 7, 6, 5],
                 [0, 4, 5, 1], [1, 5, 6, 2],
                 [2, 6, 7, 3], [4, 0, 3, 7]]

        if (divx, divy, divz) == (1, 1, 1):
            return verts, faces

        # ok, looks like we have some work to do!
        import bmesh
        import mathutils
        from mathutils import Vector

        bm = bmesh.new()
        [bm.verts.new(co) for co in verts]
        bm.normal_update()
        for face in faces:
            bm.faces.new(tuple(bm.verts[i] for i in face))
        bm.normal_update()

        dist = 0.0001
        section_dict = {0: divx, 1: divy, 2: divz}

        for axis in range(3):

            num_sections = section_dict[axis]
            if num_sections == 1:
                continue

            step = 1 / num_sections
            v1 = Vector(tuple((b if (i == axis) else 0) for i in [0, 1, 2]))
            v2 = Vector(tuple((-b if (i == axis) else 0) for i in [0, 1, 2]))

            for section in range(num_sections):
                mid_vec = v1.lerp(v2, section * step)
                plane_no = v2 - mid_vec
                plane_co = mid_vec
                visible_geom = bm.faces[:] + bm.verts[:] + bm.edges[:]

                bmesh.ops.bisect_plane(
                    bm, geom=visible_geom, dist=dist,
                    plane_co=plane_co, plane_no=plane_no,
                    use_snap_center=False,
                    clear_outer=False, clear_inner=False)

        indices = lambda face: [v.index for v in face.verts]
        verts = [v.co.to_tuple() for v in bm.verts]
        faces = [indices(face) for face in bm.faces]

        return verts, faces

    verts, faces = gen_cube()

    out_sockets = [
        ['v', 'verts', verts],
        ['s', 'faces', faces]
    ]

    return in_sockets, out_sockets

