def sv_main(pt=[], max_dist=20, ObjectID=[]):

    in_sockets = [
        ['v', 'point', pt],
        ['s', 'max_dist', max_dist],
        ['v', 'Object(ID)', ObjectID]

        ]

    import mathutils
    from mathutils import Vector

    Location = []
    Normal = []
    Index = []

    if pt:

        point = [Vector(x) for x in pt[0]]

        if ObjectID:
            obj = ObjectID[0]
        else:
            obj = [bpy.context.selected_objects]

        for i in obj:
            for i2 in i:
                for i3 in [i2.closest_point_on_mesh(p, max_dist) for p in point]:

                    Location.append((i2.matrix_world*i3[0])[:])
                    Normal.append(i3[1][:])
                    Index.append(i3[2])

    out_sockets = [
        ['v', 'Location', [Location]],
        ['v', 'Normal', [Normal]],
        ['v', 'Index', [Index]]

    ]

    return in_sockets, out_sockets
    
