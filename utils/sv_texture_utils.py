# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import gpu
from gpu_extras.batch import batch_for_shader
from sverchok.utils.modules.drawing_abstractions import drawing 

tx_vertex_shader = '''
    uniform mat4 viewProjectionMatrix;

    /* Keep in sync with intern/opencolorio/gpu_shader_display_transform_vertex.glsl */

    in vec2 texCoord;
    in vec2 pos;

    uniform float x_offset;
    uniform float y_offset;

    out vec2 texCoord_interp;

    void main()
    {
       gl_Position = viewProjectionMatrix * vec4(pos.x + x_offset, pos.y + y_offset, 0.0f, 1.0f);
       gl_Position.z = 1.0;
       texCoord_interp = texCoord;
    }
'''

tx_fragment_shader = '''
    in vec2 texCoord_interp;
    out vec4 fragColor;

    uniform sampler2D image;
    uniform bool ColorMode;

    void main()
    {
        if (ColorMode) {
           fragColor = texture(image, texCoord_interp);
        } else {
           fragColor = texture(image, texCoord_interp).rrrr;
        }
    }
'''

def init_texture(width, height, texname, texture, clr):
    drawing.init_image_from_texture(width, height, texname, texture, clr)


def simple_screen(context, args, xy):
    """ shader draw function for the texture """

    # border_color = (0.390805, 0.754022, 1.000000, 1.00)
    texture, texname, width, height, batch, shader, cMod = args
    x, y = xy

    def draw_texture(x=0, y=0, w=30, h=10, texname=texname, c=cMod):
        # function to draw a texture
        matrix = gpu.matrix.get_projection_matrix()

        drawing.disable_depth_test()
        act_tex = drawing.new_buffer_texture()
        drawing.bind_texture_2d(texname)

        shader.bind()
        shader.uniform_int("image", act_tex)
        shader.uniform_float("viewProjectionMatrix", matrix)
        shader.uniform_bool("ColorMode", c)
        shader.uniform_float("x_offset", x)
        shader.uniform_float("y_offset", y)        
        batch.draw(shader)

        # restoring settings
        drawing.bind_texture_2d(act_tex[0])
        drawing.disable_texture_2d()

    draw_texture(x=x, y=y, w=width, h=height, texname=texname, c=cMod)

gl_color_list = [
    ('BW', 'bw', 'grayscale texture', '', 0),
    ('RGB', 'rgb', 'rgb colored texture', '', 1),
    ('RGBA', 'rgba', 'rgba colored texture', '', 2)
]

gl_color_dict = {
    'BW': 6403,  # GL_RED
    'RGB': 6407,  # GL_RGB
    'RGBA': 6408  # GL_RGBA
}

factor_buffer_dict = {
    'BW': 1,  # GL_RED
    'RGB': 3,  # GL_RGB
    'RGBA': 4  # GL_RGBA
}

def get_drawing_location(node):
    x, y = node.xy_offset
    return x * node.location_theta, y * node.location_theta


def generate_batch_shader(args):
    w, h = args
    x, y = 0, 0
    positions = ((x, y), (x + w, y), (x + w, y - h), (x, y - h))
    indices = ((0, 1), (1, 1), (1, 0), (0, 0))
    shader = gpu.types.GPUShader(tx_vertex_shader, tx_fragment_shader)
    batch = batch_for_shader(shader, 'TRI_FAN', {"pos": positions, "texCoord": indices})
    return batch, shader
