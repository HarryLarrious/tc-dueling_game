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

// One font atlas texel, alpha-premultiplied.
vec4 fetch_premultiplied(ivec2 texel, ivec2 size) {
    #ifdef IS_GRAYSCALE
    vec4 c = texelFetch(Sampler0, clamp(texel, ivec2(0), size - 1), 0).rrrr;
    #else
    vec4 c = texelFetch(Sampler0, clamp(texel, ivec2(0), size - 1), 0);
    #endif
    return vec4(c.rgb * c.a, c.a);
}

// Bilinear sample at a texel-space position (the atlas sampler is NEAREST).
vec4 bilinear_premultiplied(vec2 pos, ivec2 size) {
    pos -= 0.5;
    ivec2 i = ivec2(floor(pos));
    vec2 f = fract(pos);
    vec4 top = mix(fetch_premultiplied(i, size), fetch_premultiplied(i + ivec2(1, 0), size), f.x);
    vec4 bottom = mix(fetch_premultiplied(i + ivec2(0, 1), size), fetch_premultiplied(i + ivec2(1, 1), size), f.x);
    return mix(top, bottom, f.y);
}

// Four bilinear taps spread over the pixel's footprint: plain bilinear when
// the art is magnified, a box filter when it is shrunk (no shimmer).
vec4 smooth_sample(vec2 uv, vec2 dx, vec2 dy) {
    ivec2 size = textureSize(Sampler0, 0);
    vec2 pos = uv * vec2(size);
    vec4 sum = bilinear_premultiplied(pos + 0.25 * (dx + dy), size)
        + bilinear_premultiplied(pos + 0.25 * (dx - dy), size)
        + bilinear_premultiplied(pos - 0.25 * (dx - dy), size)
        + bilinear_premultiplied(pos - 0.25 * (dx + dy), size);
    sum *= 0.25;
    return sum.a > 0.0 ? vec4(sum.rgb / sum.a, sum.a) : vec4(0.0);
}

void main() {
    // Derivatives outside any branch (texel-space footprint of this pixel).
    vec2 atlasSize = vec2(textureSize(Sampler0, 0));
    vec2 dx = dFdx(texCoord0 * atlasSize);
    vec2 dy = dFdy(texCoord0 * atlasSize);

    vec4 texColor;
    if (uiSmooth > 0.5) {
        texColor = smooth_sample(texCoord0, dx, dy);
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
