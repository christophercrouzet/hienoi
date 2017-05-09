#version 330 core

in data
{
    vec4 color;
} In;

layout(location=0) out vec4 out_color;


void
main()
{
    out_color = vec4(In.color);
}
