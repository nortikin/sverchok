import bpy
import numpy as np

"""
Sample an image at u,v coordinates.
Images can either be selected by name or int.
"""

def clip(low, high, val):
    return min(high, max(low, val))

def sv_main(img_name=0, p=[[[0,0,0]]]):
    in_sockets = [
       ['s', "Image name", img_name],
       ['v', 'Point', p],
    ]
    def get_name(img_name):
        if isinstance(img_name, (str, int)):
            return img_name
        elif img_name:
            return get_name(img_name[0])
        else:
            0
    def get_name(img_name):
        if isinstance(img_name, (str, int)):
            return img_name
        elif img_name:
            return get_name(img_name[0])
        else:
            0
    img_name = get_name(img_name)
    # if you want to look to a specific image
    #img_name = "Emperor_Penguin_Manchot_empereur.jpg"


    dim_x, dim_y = bpy.data.images[img_name].size
    tmp = np.array(bpy.data.images[img_name].pixels)
    image = tmp.reshape(dim_y, dim_x, 4)
    out = []
    if p:
        for point in p[0]:
            x,y, _ = point
            u_i = clip(0, dim_x - 1, int(x * dim_x))
            v_i = clip(0, dim_y - 1, int(y*dim_y))

            color = image[v_i, u_i][:3]

            out.append(color)


    out_sockets = [
        ['v', 'Color', [out]]
    ]

    return in_sockets, out_sockets
