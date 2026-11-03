#version 330
#extension GL_ARB_separate_shader_objects : require

// Screen effects on the world image (minecraft:main), driven by the marker
// in the outline image (mech:fx.glsl). Runs inside the entity_outline chain,
// which the game runs before the hand and the GUI: the HUD never zooms,
// shakes or tints. Pulses and noise run on GameTime, so the server only
// sends a new marker color when an effect starts or stops.

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

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

// 0 at the screen center, 1 at the corners (aspect corrected).
float edge(vec2 uv) {
    vec2 d = (uv - 0.5) * vec2(OutSize.x / OutSize.y, 1.0);
    return length(d) / length(vec2(0.5 * OutSize.x / OutSize.y, 0.5));
}

void main() {
    ivec3 marker = mech_decode_marker(texelFetch(OutlineSampler, ivec2(0), 0));
    int effects = marker.z < 0 ? 0 : marker.x;
    float strength = float(marker.y) / 255.0;
    float t = GameTime * 1200.0;  // seconds, wraps daily
    vec2 uv = texCoord;
    bool zoom = (effects & MECH_FX_ZOOM) != 0;
    bool emp = (effects & MECH_FX_EMP) != 0;

    if (zoom) {
        // Up to 3x digital zoom about the screen center.
        uv = 0.5 + (uv - 0.5) / (1.0 + 2.0 * strength);
    }
    if ((effects & MECH_FX_SHAKE) != 0) {
        vec2 jitter = vec2(sin(t * 91.0) + 0.5 * sin(t * 47.0), cos(t * 83.0) + 0.5 * cos(t * 59.0));
        uv += jitter * 0.008;
    }
    float split = 0.0;
    if (emp) {
        // Glitch: a few horizontal bands jump sideways, re-rolled 12x/s.
        float frame = floor(t * 12.0);
        float band = floor(uv.y * 24.0);
        float roll = hash(vec2(band, frame));
        if (roll > 0.82) {
            uv.x += (hash(vec2(frame, band)) - 0.5) * 0.08;
        }
        split = 0.004 + 0.004 * hash(vec2(frame, 7.0));
    }

    vec2 cuv = clamp(uv, vec2(0.0), vec2(1.0));
    vec4 color = texture(InSampler, cuv);
    if (split > 0.0) {
        color.r = texture(InSampler, clamp(uv + vec2(split, 0.0), vec2(0.0), vec2(1.0))).r;
        color.b = texture(InSampler, clamp(uv - vec2(split, 0.0), vec2(0.0), vec2(1.0))).b;
    }

    float e = edge(texCoord);
    if ((effects & MECH_FX_GRAY) != 0) {
        // Destroyed: desaturate, then fade toward dark as strength rises.
        float luma = dot(color.rgb, vec3(0.2126, 0.7152, 0.0722));
        color.rgb = mix(color.rgb, vec3(luma), min(1.0, 0.5 + strength));
        color.rgb *= 1.0 - 0.75 * strength;
    }
    if ((effects & MECH_FX_TINT) != 0 && !zoom) {
        // Damage flash: push toward red, darken the edges.
        float vignette = smoothstep(0.35, 0.95, e);
        vec3 red = color.rgb * vec3(1.0, 0.35, 0.3) + vec3(0.22, 0.0, 0.0);
        color.rgb = mix(color.rgb, red, strength * (0.45 + 0.55 * vignette));
    }
    if (emp) {
        // Static: per-pixel noise at 30 fps, plus rolling dark lines.
        vec2 px = floor(texCoord * OutSize / 2.0);
        float n = hash(px + floor(t * 30.0));
        color.rgb = mix(color.rgb, vec3(n), 0.28);
        float roll = fract(texCoord.y * 3.0 - t * 0.7);
        color.rgb *= 0.85 + 0.15 * smoothstep(0.0, 0.08, roll);
    }
    if ((effects & MECH_FX_SHAKE) != 0) {
        // Flash: a short bright flicker on top of the shake.
        color.rgb += vec3(1.0, 0.85, 0.6) * 0.18 * max(0.0, sin(t * 40.0));
    }
    if ((effects & MECH_FX_HRB) != 0) {
        // Strike-zone warning: red edges pulsing twice a second.
        float pulse = 0.5 + 0.5 * sin(t * 12.566);
        float ring = smoothstep(0.45, 1.0, e);
        color.rgb = mix(color.rgb, vec3(1.0, 0.08, 0.05), ring * (0.25 + 0.45 * pulse));
    }
    if ((effects & MECH_FX_LOWHP) != 0) {
        // Heartbeat: two quick red edge pulses every 1.1 s.
        float beat = fract(t / 1.1);
        float pulse = exp(-40.0 * beat * beat) + 0.6 * exp(-40.0 * (beat - 0.22) * (beat - 0.22));
        float ring = smoothstep(0.55, 1.05, e);
        color.rgb = mix(color.rgb, vec3(0.75, 0.0, 0.0), ring * min(1.0, 0.25 + 0.6 * pulse));
    }
    if ((effects & MECH_FX_VISOR) != 0) {
        // Cockpit visor: faint scanlines, a soft vignette, cool edges.
        float line = 0.97 + 0.03 * step(0.5, fract(gl_FragCoord.y / 3.0));
        color.rgb *= line;
        float vig = smoothstep(0.55, 1.15, e);
        color.rgb = mix(color.rgb, color.rgb * vec3(0.55, 0.75, 0.85), vig * 0.6);
    }
    if (zoom) {
        // Scope frame: dark outside a circle, a thin bright ring at its edge.
        vec2 d = (texCoord - 0.5) * vec2(OutSize.x / OutSize.y, 1.0);
        float r = length(d);
        float outside = smoothstep(0.44, 0.47, r);
        float ring = smoothstep(0.425, 0.44, r) * (1.0 - smoothstep(0.44, 0.455, r));
        color.rgb = mix(color.rgb, color.rgb * 0.12, outside);
        color.rgb += vec3(0.45, 0.85, 1.0) * ring * 0.6;
    }

    fragColor = vec4(color.rgb, 1.0);
}
