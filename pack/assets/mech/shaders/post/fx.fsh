#version 330
#extension GL_ARB_separate_shader_objects : require

// Screen effects on the world image (minecraft:main), driven by the marker
// in the outline image (mech:fx.glsl). Runs inside the entity_outline chain,
// which the game runs before the hand and the GUI: the HUD never zooms,
// shakes or tints.

#include <minecraft:globals.glsl>
#include <mech:fx.glsl>

uniform sampler2D InSampler;
uniform sampler2D OutlineSampler;

layout(std140) uniform SamplerInfo {
    vec2 OutSize;
    vec2 InSize;
    vec2 OutlineSize;
};

layout(location = 0) in vec2 texCoord;

layout(location = 0) out vec4 fragColor;

void main() {
    ivec3 marker = mech_decode_marker(texelFetch(OutlineSampler, ivec2(0), 0));
    int effects = marker.z < 0 ? 0 : marker.x;
    float strength = float(marker.y) / 255.0;
    vec2 uv = texCoord;

    if ((effects & MECH_FX_ZOOM) != 0) {
        // Up to 3x digital zoom about the screen center.
        uv = 0.5 + (uv - 0.5) / (1.0 + 2.0 * strength);
    }
    if ((effects & MECH_FX_SHAKE) != 0) {
        float t = GameTime * 1200.0;  // seconds
        vec2 jitter = vec2(sin(t * 91.0) + 0.5 * sin(t * 47.0), cos(t * 83.0) + 0.5 * cos(t * 59.0));
        uv += jitter * strength * 0.012;
    }

    vec4 color = texture(InSampler, clamp(uv, vec2(0.0), vec2(1.0)));

    if ((effects & MECH_FX_GRAY) != 0) {
        float luma = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
        color.rgb = mix(color.rgb, vec3(luma), strength);
    }
    if ((effects & MECH_FX_TINT) != 0) {
        // Damage flash: push toward red, darken the edges.
        vec2 d = texCoord - 0.5;
        float vignette = smoothstep(0.25, 0.75, length(d * vec2(OutSize.x / OutSize.y, 1.0)));
        vec3 red = color.rgb * vec3(1.0, 0.35, 0.3) + vec3(0.22, 0.0, 0.0);
        color.rgb = mix(color.rgb, red, strength * (0.45 + 0.55 * vignette));
    }

    fragColor = vec4(color.rgb, 1.0);
}
