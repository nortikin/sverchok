# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

tx_vertex_shader = '''
    uniform mat4 ModelViewProjectionMatrix;

    /* Keep in sync with intern/opencolorio/gpu_shader_display_transform_vertex.glsl */

    in vec2 texCoord;
    in vec2 pos;

    uniform float x_offset;
    uniform float y_offset;

    out vec2 texCoord_interp;

    void main()
    {
       gl_Position = ModelViewProjectionMatrix * vec4(pos.x + x_offset, pos.y + y_offset, 0.0f, 1.0f);
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
    # function to init the texture
    bgl.glPixelStorei(bgl.GL_UNPACK_ALIGNMENT, 1)

    bgl.glEnable(bgl.GL_TEXTURE_2D)
    bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)
    bgl.glActiveTexture(bgl.GL_TEXTURE0)

    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_S, bgl.GL_CLAMP_TO_EDGE)
    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_WRAP_T, bgl.GL_CLAMP_TO_EDGE)
    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MAG_FILTER, bgl.GL_LINEAR)
    bgl.glTexParameterf(bgl.GL_TEXTURE_2D, bgl.GL_TEXTURE_MIN_FILTER, bgl.GL_LINEAR)

    bgl.glTexImage2D(
        bgl.GL_TEXTURE_2D,
        0, clr, width, height,
        0, clr, bgl.GL_FLOAT, texture
    )


def simple_screen(x, y, args):
    """ shader draw function for the texture """

    # border_color = (0.390805, 0.754022, 1.000000, 1.00)
    texture, texname, width, height, batch, shader, cMod = args

    def draw_texture(x=0, y=0, w=30, h=10, texname=texname, c=cMod):
        # function to draw a texture
        bgl.glDisable(bgl.GL_DEPTH_TEST)

        act_tex = bgl.Buffer(bgl.GL_INT, 1)
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, texname)

        shader.bind()
        shader.uniform_int("image", act_tex)
        shader.uniform_bool("ColorMode", c)
        shader.uniform_float("x_offset", x)
        shader.uniform_float("y_offset", y)        
        batch.draw(shader)

        # restoring settings
        bgl.glBindTexture(bgl.GL_TEXTURE_2D, act_tex[0])
        bgl.glDisable(bgl.GL_TEXTURE_2D)

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