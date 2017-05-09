#version 330 core

uniform bool fill;

in data
{
    flat vec4 color;
    vec2 coord;
    flat float half_edge_feather;  //< Relative to the billboard size.
    flat float half_stroke_width;  //< Relative to the billboard size.
} In;

layout(location=0) out vec4 out_color;


void
main()
{
    float distance_to_edge = 1.0 - length(In.coord);
    float fill_alpha = smoothstep(
        -In.half_edge_feather,
        In.half_edge_feather,
        distance_to_edge
    );
    float stroke_alpha = smoothstep(
        In.half_edge_feather,
        0.0,
        abs(distance_to_edge) - In.half_stroke_width
    );
    float alpha = mix(stroke_alpha, fill_alpha, fill);
    out_color = vec4(In.color.rgb, In.color.a * alpha);
}
