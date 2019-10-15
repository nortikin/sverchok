# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import gpu
from gpu_extras.batch import batch_for_shader


vertex_shader = '''
    layout (location = 0) in vec3 inPos;

    flat out vec3 startPos;
    out vec3 vertPos;

    uniform mat4 u_mvp;

    void main()
    {
        vec4 pos    = u_mvp * vec4(inPos, 1.0);
        gl_Position = pos;
        vertPos     = pos.xyz / pos.w;
        startPos    = vertPos;
    }
'''

geometry_shader = '''




'''

fragment_shader = '''
    flat in vec3 startPos;
    in vec3 vertPos;

    out vec4 fragColor;

    uniform vec2  u_resolution;
    uniform vec4  m_color;
    uniform float u_dashSize;
    uniform float u_gapSize;

    void main()
    {
        vec2  dir  = (vertPos.xy-startPos.xy) * u_resolution/2.0;
        float dist = length(dir);

        if (fract(dist / (u_dashSize + u_gapSize)) > u_dashSize/(u_dashSize + u_gapSize))
            discard; 
        fragColor = m_color;
    }
'''


def draw_function(context, args):
    
    shader = gpu.types.GPUShader(args.v_shader, args.f_shader, geocode=args.g_shader)
    batch = batch_for_shader(shader, 'LINES', {"pos" : args.coords}, indices=args.indices)

    shader.bind()
    matrix = context.region_data.perspective_matrix
    shader.uniform_float("u_mvp", matrix)
    shader.uniform_float("u_resolution", args.u_resolution)
    shader.uniform_float("u_dashSize", args.u_dash_size)    
    shader.uniform_float("u_gapSize", args.u_gap_size)
    shader.uniform_float("m_color", args.line4f)

    batch.draw(shader)


def get_shader_config():
    shader = lambda: None
    shader.v_shader = vertex_shader
    shader.g_shader = geometry_shader
    shader.f_shader = fragment_shader
    shader.draw_function = draw_function
    return shader

