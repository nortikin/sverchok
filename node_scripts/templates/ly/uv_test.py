import bpy
import numpy as np



def sv_main(idx=0, obj_name=0):
    in_sockets = [
       ['s', "Index", idx],
       ['s', "Object name", obj_name]
    ]

    def get_name(img_name):
        if isinstance(img_name, (str, int)):
            return img_name
        elif img_name:
            return get_name(img_name[0])
        else:
            0
    obj_name = get_name(obj_name)
    # if you want to look to a specific image
    #obj_name = "Suzanne"
    if str(obj_name) in bpy.data.objects:

        obj = bpy.data.objects[obj_name]
        print(obj.name)
        mesh = obj.data
        uv_layer = mesh.uv_layers.active
    out = []
    if idx:

        for i in idx:
            u, v = uv_layer.data[i].uv
            out.append((u,v, 0))

    out_sockets = [
        ['v', 'UV', [out]]
    ]

    return in_sockets, out_sockets
