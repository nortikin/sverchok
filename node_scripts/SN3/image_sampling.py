import bpy
import numpy as np


"""
Sample an image at u,v coordinates, repeatin the texture
Images can either be selected by name or int.
Outputs image data at uv as rgb
"""

def draw(self, context, layout):
    layout.prop_search(self, "image_name", bpy.data, "images")

@node_script(draw_buttons=draw)
def sample_image(
        image_name: StringP(name="Image") = "",
        points: Vertex("Uv points") = None
        ) -> (
        Vertex("Colors"),
        Float("Alpha")):

    bpy_image = bpy.data.images[image_name]

    dim_x, dim_y = bpy_image.size
    image = np.array(bpy_image.pixels[:]).reshape(dim_y, dim_x, 4)

    out = []
    alpha = []
    points = np.array(points[0])
    uv = points * (dim_x, dim_y, 0)

    for u, v, _ in uv:
        color = image[v % dim_y, u % dim_x]
        out.append(color[:3].tolist())
        alpha.append(color[-1])

    return out, alpha
