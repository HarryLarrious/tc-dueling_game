#version 330
#extension GL_ARB_separate_shader_objects : require

// First step of the outline chain: removes the screen-effect marker from the
// outline image, and keeps only the outlines in the viewer's party color
// (party from the marker, mech:fx.glsl). Without a marker every outline is
// kept, as vanilla.

#include <mech:fx.glsl>

uniform sampler2D InSampler;

layout(std140) uniform SamplerInfo {
    vec2 OutSize;
    vec2 InSize;
};

layout(location = 0) in vec2 texCoord;

layout(location = 0) out vec4 fragColor;

void main() {
    ivec2 pixel = ivec2(texCoord * InSize);
    if (all(lessThan(pixel, ivec2(MECH_MARKER_SIZE)))) {
        fragColor = vec4(0.0);
        return;
    }

    vec4 color = texelFetch(InSampler, pixel, 0);
    int party = mech_decode_marker(texelFetch(InSampler, ivec2(0), 0)).z;
    if (party == MECH_PARTY_NONE) {
        color = vec4(0.0);
    } else if (party > MECH_PARTY_ALL && color.a > 0.0) {
        vec3 diff = abs(color.rgb - mech_party_color(party));
        if (max(diff.r, max(diff.g, diff.b)) > 1.5 / 255.0) {
            color = vec4(0.0);
        }
    }
    fragColor = color;
}
