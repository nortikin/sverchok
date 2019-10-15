# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#  
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE



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
    ...


def get_shader():
    shader = lambda: None
    shader.vertex_shader = vertex_shader
    shader.geometry_shader = geometry_shader
    shader.fragment_shader = fragment_shader
    shader.draw_function = draw_function
    return shader

