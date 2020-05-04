"""
in   in_data    v  d=[]  n=1
in   in_colors  v  d=[]  n=1
out  float_out  s
"""

import bgl
import bpy
from gpu_extras.batch import batch_for_shader
import gpu

from sverchok.data_structure import node_id
from sverchok.ui import bgl_callback_3dview as v3dBGL

self.n_id = node_id(self)
v3dBGL.callback_disable(self.n_id)


def screen_v3dBGL(context, args):

    points = args[0]
    colors = args[1]  # expects 4-tuple r g b a
    shader = gpu.shader.from_builtin('3D_SMOOTH_COLOR')
    batch = batch_for_shader(shader, 'POINTS', {"pos": points, "color": colors})
    batch.draw(shader)


if self.inputs['in_data'].links:

    draw_data = {
        'tree_name': self.id_data.name[:],
        'custom_function': screen_v3dBGL,
        'args': (in_data, in_colors)
    }

    v3dBGL.callback_enable(self.n_id, draw_data, overlay='POST_VIEW')
