# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

#
#  shader hoisted from https://stackoverflow.com/questions/52928678/dashed-line-in-opengl3
#

import sverchok


dashed_vertex_shader = '''
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

dashed_fragment_shader = '''
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

def screen_v3dBGL_dashed(context, args):
    # region = context.region
    # region3d = context.space_data.region_3d
    matrix = context.region_data.perspective_matrix
    
    shader = args.shader
    batch = args.batch

    shader.bind()
    shader.uniform_float("u_mvp", matrix)
    shader.uniform_float("u_resolution", args.u_resolution)
    shader.uniform_float("u_dashSize", args.u_dash_size)    
    shader.uniform_float("u_gapSize", args.u_gap_size)
    shader.uniform_float("m_color", args.line4f)

    batch.draw(shader)


##### -----------------------------------------------------------------------
#
#     line thickness shader   .woohooo! 
#
#     https://docs.blender.org/api/blender2.8/gpu.types.html#gpu.types.GPUShader
#
##### -----------------------------------------------------------------------


line_shader = sverchok.utils.modules.line_shader.get_shader()
