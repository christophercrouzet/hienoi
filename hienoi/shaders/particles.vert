#version 330 core

uniform mat4 projection;
uniform float half_edge_feather;  //< In world unit.
uniform float half_stroke_width;  //< In world unit.
uniform bool fill;

layout(location=0) in vec2 in_position;
layout(location=1) in float in_size;
layout(location=2) in vec4 in_color;

out data
{
    flat vec4 color;
    vec2 coord;
    flat float half_edge_feather;  //< Relative to the billboard size.
    flat float half_stroke_width;  //< Relative to the billboard size.
} Out;

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
    Out.color = in_color;
    Out.half_edge_feather = half_edge_feather / in_size;
    Out.half_stroke_width = half_stroke_width / in_size;

    // Compute the billboard coordinates where a length of 1 represents
    // the radius of the particle. An extra padding is added to allow drawing
    // edge feathering and possibly a centered stroke with a given width.
    vec2 vertex_position = VERTEX_POSITIONS[gl_VertexID % VERTEX_COUNT];
    float padding =
        Out.half_edge_feather + Out.half_stroke_width * (1.0 - float(fill));
    Out.coord = vertex_position * (1.0 + padding);

    gl_Position = projection
                  * vec4(in_position + Out.coord * in_size, 0.0, 1.0);
}
