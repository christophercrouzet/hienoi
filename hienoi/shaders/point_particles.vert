#version 330 core

uniform mat4 projection;

layout(location=0) in vec2 in_position;
layout(location=1) in vec4 in_color;

out data
{
    vec4 color;
} Out;


void
main()
{
    gl_Position = projection * vec4(in_position, 0.0, 1.0);
    Out.color = in_color;
}
