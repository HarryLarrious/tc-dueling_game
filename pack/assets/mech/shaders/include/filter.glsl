#ifndef MECH_FILTER_GLSL
#define MECH_FILTER_GLSL

// Smooth sampling for high-resolution art in atlases whose sampler is
// NEAREST (font pages, the item atlas): bilinear when magnified, a 4-tap
// footprint average when shrunk, on premultiplied colors so transparent
// texels do not darken edges. Define MECH_FILTER_GRAYSCALE first for
// single-channel textures (read as .rrrr).

vec4 mech_texel_premultiplied(sampler2D tex, ivec2 texel, ivec2 size) {
    #ifdef MECH_FILTER_GRAYSCALE
    vec4 c = texelFetch(tex, clamp(texel, ivec2(0), size - 1), 0).rrrr;
    #else
    vec4 c = texelFetch(tex, clamp(texel, ivec2(0), size - 1), 0);
    #endif
    return vec4(c.rgb * c.a, c.a);
}

// Bilinear sample at a texel-space position.
vec4 mech_bilinear_premultiplied(sampler2D tex, vec2 pos, ivec2 size) {
    pos -= 0.5;
    ivec2 i = ivec2(floor(pos));
    vec2 f = fract(pos);
    vec4 top = mix(mech_texel_premultiplied(tex, i, size), mech_texel_premultiplied(tex, i + ivec2(1, 0), size), f.x);
    vec4 bottom = mix(mech_texel_premultiplied(tex, i + ivec2(0, 1), size), mech_texel_premultiplied(tex, i + ivec2(1, 1), size), f.x);
    return mix(top, bottom, f.y);
}

// dx, dy: dFdx / dFdy of uv * textureSize, taken by the caller outside any
// branch.
vec4 mech_smooth_sample(sampler2D tex, vec2 uv, vec2 dx, vec2 dy) {
    ivec2 size = textureSize(tex, 0);
    vec2 pos = uv * vec2(size);
    vec4 sum = mech_bilinear_premultiplied(tex, pos + 0.25 * (dx + dy), size)
        + mech_bilinear_premultiplied(tex, pos + 0.25 * (dx - dy), size)
        + mech_bilinear_premultiplied(tex, pos - 0.25 * (dx - dy), size)
        + mech_bilinear_premultiplied(tex, pos - 0.25 * (dx + dy), size);
    sum *= 0.25;
    return sum.a > 0.0 ? vec4(sum.rgb / sum.a, sum.a) : vec4(0.0);
}

#endif
