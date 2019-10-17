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
    /* 

    takes an edge
    takes a quantity "number of segments"

    returns several perpendicular edges, to thicken lines

    */

    layout(lines) in;
    layout(line_strip, max_vertices = 2) out;

    void main() {
      for(int i = 0; i < 2; i++) {
        gl_Position = gl_in[i].gl_Position + vec4(1.0, 0.0, 0.0, 0.0);
        EmitVertex();
      }
      EndPrimitive();
    }



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
    args, config = args
    
    shader = gpu.types.GPUShader(config.v_shader, config.f_shader, geocode=config.g_shader)
    batch = batch_for_shader(shader, 'LINES', {"pos" : args.coords}, indices=args.indices)

    shader.bind()
    matrix = context.region_data.perspective_matrix
    shader.uniform_float("u_mvp", matrix)
    shader.uniform_float("u_resolution", args.u_resolution)
    shader.uniform_float("u_dashSize", args.u_dash_size)    
    shader.uniform_float("u_gapSize", args.u_gap_size)
    shader.uniform_float("m_color", args.line4f)
    # shader.uniform_float("u_offset", args.u_offset)
    # shader.uniform_float("u_num_segs", args.u_num_segs)

    batch.draw(shader)


def get_shader_config():
    config = lambda: None
    config.v_shader = vertex_shader
    config.g_shader = geometry_shader
    config.f_shader = fragment_shader
    config.draw_function = draw_function
    return config

