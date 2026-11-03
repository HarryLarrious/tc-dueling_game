#version 330
#extension GL_ARB_separate_shader_objects : require

// Vanilla 26.3 core/text.fsh, except marked UI glyphs (uiSmooth = 1, set in
// text.vsh) are sampled filtered instead of nearest: their art is high
// resolution and must look smooth at any window size. Unmarked text is
// sampled exactly as vanilla.

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
#include <minecraft:fog.glsl>
#endif

#include <minecraft:dynamictransforms.glsl>
#include <minecraft:oit.glsl>
#ifdef IS_GRAYSCALE
#define MECH_FILTER_GRAYSCALE
#endif
#include <mech:filter.glsl>

uniform sampler2D Sampler0;

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
#endif

layout(location = 2) in vec4 vertexColor;
layout(location = 3) in vec2 texCoord0;
layout(location = 4) in float uiSmooth;

#ifndef OIT_ALPHA_ONLY
layout(location = 0) out vec4 fragColor;
#endif

vec4 calculateFinalColor(vec4 color) {
    #ifdef OIT_ACCUMULATE
    color = sampleColorForAccumulation(color);
    #endif

    #if !defined(IS_SEE_THROUGH) && !defined(IS_GUI)

    #ifdef OIT_ACCUMULATE
    vec4 fogColor = vec4(FogColor.rgb * color.a, FogColor.a);
    #else
    vec4 fogColor = FogColor;
    #endif

    color = apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, fogColor);
    #endif

    return color;
}

void main() {
    // Derivatives outside any branch (texel-space footprint of this pixel).
    vec2 atlasSize = vec2(textureSize(Sampler0, 0));
    vec2 dx = dFdx(texCoord0 * atlasSize);
    vec2 dy = dFdy(texCoord0 * atlasSize);

    vec4 texColor;
    if (uiSmooth > 0.5) {
        texColor = mech_smooth_sample(Sampler0, texCoord0, dx, dy);
    } else {
        #ifdef IS_GRAYSCALE
        texColor = texture(Sampler0, texCoord0).rrrr;
        #else
        texColor = texture(Sampler0, texCoord0);
        #endif
    }

    vec4 color = texColor * vertexColor * ColorModulator;

    if (color.a < 0.1) {
        discard;
    }

    #ifdef OIT_ALPHA_ONLY
    executeAlphaOnlyPhase(gl_FragCoord.z, color.a);
    #else
    fragColor = calculateFinalColor(color);
    #endif
}
