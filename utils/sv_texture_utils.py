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
