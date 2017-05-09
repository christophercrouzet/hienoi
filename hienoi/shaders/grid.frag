#version 330 core

uniform ivec2 origin;
uniform float unit;
uniform vec4 color;
uniform vec4 origin_color;

layout(location=0) out vec4 out_color;

const vec4 default_color = vec4(0.0);


void
main()
{
    ivec2 coord = ivec2(gl_FragCoord.xy);

    out_color = default_color;

    bool on_grid = any(equal(floor(mod(origin - coord, unit)), ivec2(0)));
    out_color = mix(out_color, color, float(on_grid));

    bool on_grid_origin = any(equal(coord, origin));
    out_color = mix(out_color, origin_color, float(on_grid_origin));
}
