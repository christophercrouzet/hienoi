#version 330 core

const int VERTEX_COUNT = 4;
const vec2 VERTEX_POSITIONS[VERTEX_COUNT] = vec2[](
    vec2(-1.0, -1.0),
    vec2(-1.0,  1.0),
    vec2( 1.0, -1.0),
    vec2( 1.0,  1.0)
);


void
main()
{
    gl_Position = vec4(VERTEX_POSITIONS[gl_VertexID], 0.0, 1.0);
}
