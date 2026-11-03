#version 330
#extension GL_ARB_separate_shader_objects : require

// Vanilla 26.3 core/item.fsh, plus (PLAN.md, Client-side tech and Art
// quality):
//   Emissive pixels: texture alpha 250 = full bright and opaque, 251 = the
//     same, pulsing with GameTime. No lightmap, no shading, any variant.
//   World items (inWorld = 1, mech parts on item displays): smooth sampling
//     of high-resolution textures and per-pixel lighting instead of
//     vanilla's flat two-light shading. The lightmap still applies, so
//     night is dark. GUI items render exactly as vanilla.

#include <minecraft:globals.glsl>
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:oit.glsl>
#include <mech:filter.glsl>

uniform sampler2D Sampler0;

#ifdef GLINT
uniform sampler2D GlintSampler;
#endif

#ifndef OIT_ALPHA_ONLY
layout(location = 0) in float sphericalVertexDistance;
layout(location = 1) in float cylindricalVertexDistance;
#endif
layout(location = 2) in vec4 vertexColor;
#ifndef OIT_ALPHA_ONLY
layout(location = 3) in vec4 lightMapColor;
layout(location = 4) in vec4 overlayColor;
#endif
layout(location = 5) in vec2 texCoord0;
#ifdef GLINT
layout(location = 6) in vec2 texCoordGlint;
#endif
layout(location = 7) in float inWorld;
layout(location = 8) in vec3 worldNormal;
layout(location = 9) in vec3 cameraOffset;

#ifndef OIT_ALPHA_ONLY
layout(location = 0) out vec4 fragColor;
#endif

// Reserved texture alphas (pack/src/spike_assets.py uses the same values).
const int EMISSIVE_ALPHA = 250;
const int EMISSIVE_PULSE_ALPHA = 251;
// Pulses per second; GameTime runs 0..1 over a 24000-tick (1200 s) day.
const float PULSE_HZ = 1.0;

// World lighting: a warm key light from above, a sky/ground ambient, a small
// specular highlight and a cool rim on silhouettes.
const vec3 KEY_DIR = vec3(0.3612, 0.8771, 0.3164);  // normalize(0.35, 0.85, 0.4)
const vec3 KEY_COLOR = vec3(0.64, 0.61, 0.57);
const vec3 SKY_AMBIENT = vec3(0.50, 0.54, 0.60);
const vec3 GROUND_AMBIENT = vec3(0.26, 0.25, 0.24);
const vec3 RIM_COLOR = vec3(0.45, 0.65, 0.85);

vec3 shade_world(vec3 albedo, vec3 normal, vec3 toCamera) {
    vec3 n = normalize(normal);
    vec3 v = normalize(toCamera);
    vec3 ambient = mix(GROUND_AMBIENT, SKY_AMBIENT, n.y * 0.5 + 0.5);
    // Wrapped diffuse: soft falloff instead of a hard terminator.
    float key = max((dot(n, KEY_DIR) + 0.3) / 1.3, 0.0);
    float spec = dot(n, KEY_DIR) > 0.0 ? pow(max(dot(n, normalize(KEY_DIR + v)), 0.0), 40.0) * 0.22 : 0.0;
    float rim = pow(1.0 - max(dot(n, v), 0.0), 3.0) * 0.25;
    return albedo * (ambient + KEY_COLOR * key) + vec3(spec) + RIM_COLOR * rim;
}

#ifndef OIT_ALPHA_ONLY
vec4 calculateFinalColor(vec4 color, bool emissive) {
    if (!emissive) {
        color.rgb = mix(overlayColor.rgb, color.rgb, overlayColor.a);
        color *= lightMapColor;
    }

    #ifdef GLINT
    vec4 glintColor = GlintAlpha * texture(GlintSampler, texCoordGlint);// Glint color modulator?
    // Matches BlendFuntion.GLINT
    color.rgb += glintColor.rgb * glintColor.rgb;
    #endif

    #ifdef OIT_ACCUMULATE
    color = sampleColorForAccumulation(color);
    vec4 fogColor = vec4(FogColor.rgb * color.a, FogColor.a);
    #else
    vec4 fogColor = FogColor;
    #endif

    return apply_fog(color, sphericalVertexDistance, cylindricalVertexDistance, FogEnvironmentalStart, FogEnvironmentalEnd, FogRenderDistanceStart, FogRenderDistanceEnd, fogColor);
}
#endif

void main() {
    // Derivatives outside any branch (texel-space footprint of this pixel).
    vec2 atlasSize = vec2(textureSize(Sampler0, 0));
    vec2 dx = dFdx(texCoord0 * atlasSize);
    vec2 dy = dFdy(texCoord0 * atlasSize);

    // The exact texel (the sampler is NEAREST) carries the emissive marker.
    vec4 texel = texture(Sampler0, texCoord0);
    int markerAlpha = int(round(texel.a * 255.0));
    bool emissive = markerAlpha == EMISSIVE_ALPHA || markerAlpha == EMISSIVE_PULSE_ALPHA;
    bool world = inWorld > 0.5;

    vec4 color = world ? mech_smooth_sample(Sampler0, texCoord0, dx, dy) : texel;

    if (emissive) {
        color = vec4(color.rgb, 1.0);
        if (markerAlpha == EMISSIVE_PULSE_ALPHA) {
            color.rgb *= 0.55 + 0.45 * sin(GameTime * 1200.0 * 6.2831853 * PULSE_HZ);
        }
    } else {
        #ifdef ALPHA_CUTOUT
        if (color.a < ALPHA_CUTOUT) {
            discard;
        }
        #endif
        color *= vertexColor * ColorModulator;
        if (world) {
            color.rgb = shade_world(color.rgb, worldNormal, -cameraOffset);
        }
    }

    #ifdef GLINT
    color.a = max(color.a, GlintAlpha);
    #endif

    #ifdef OIT_ALPHA_ONLY
    executeAlphaOnlyPhase(gl_FragCoord.z, color.a);
    #else
    fragColor = calculateFinalColor(color, emissive);
    #endif
}
