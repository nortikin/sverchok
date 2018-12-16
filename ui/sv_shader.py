vertex_shader = '''
    uniform mat4 ModelViewProjectionMatrix;
/* Keep in sync with intern/opencolorio/gpu_shader_display_transform_vertex.glsl */
    in vec2 texCoord;
    in vec2 pos;

    out vec2 texCoord_interp;

    void main()
    {
       gl_Position = ModelViewProjectionMatrix * vec4(pos.xy, 0.0f, 1.0f);
       gl_Position.z = 1.0;
       texCoord_interp = texCoord;
    }
'''

fragment_shader = '''

    in vec2 texCoord_interp;
    out vec4 fragColor;

    uniform sampler2D image;

    void main()
    {
        # gl_FragColor = vec4(pos * brightness, 1.0);
        vec4 col = texture(image, texCoord_interp);
        fragColor = (col.x,col.x,col.x,0.0)
        # fragColor = texture(image, texCoord_interp);
    }
'''
