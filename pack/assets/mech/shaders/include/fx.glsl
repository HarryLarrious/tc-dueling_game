#ifndef MECH_FX_GLSL
#define MECH_FX_GLSL

// Screen-effect marker (PLAN.md, Client-side tech → Post effects): each
// player has one tiny glowing display only they see. Its glow color is
//   red   = effects bitmask (MECH_FX_*)
//   green = strength 0..255
//   blue  = 240 + party: 0 shows every outline, 1..14 only that party's
//           color, 15 none
// Glow colors with blue >= 240 are reserved for the marker; party colors
// (mech_party_color) keep every channel <= 230.

const int MECH_FX_ZOOM = 1;     // digital zoom 1..3x by strength, scope frame
const int MECH_FX_SHAKE = 2;    // shake + flash (big hits, recoil, landings)
const int MECH_FX_TINT = 4;     // red damage tint with vignette
const int MECH_FX_GRAY = 8;     // desaturate + fade to dark by strength (destroyed)
const int MECH_FX_EMP = 16;     // static, glitch lines, color split
const int MECH_FX_HRB = 32;     // red warning pulse (in an HRB strike zone)
const int MECH_FX_VISOR = 64;   // always-on cockpit visor: scanlines, vignette
const int MECH_FX_LOWHP = 128;  // heartbeat edge pulse at low HP
// Strength drives zoom when MECH_FX_ZOOM is set; otherwise tint and fade.

const int MECH_PARTY_ALL = 0;
const int MECH_PARTY_NONE = 15;

// The marker covers a MECH_MARKER_SIZE square of outline pixels at the
// corner drawn at NDC (-1, -1), read back as texel (0, 0).
const int MECH_MARKER_SIZE = 2;

bool mech_is_marker(vec3 color) {
    return int(round(color.b * 255.0)) >= 240;
}

// Returns (effects, strength 0..255, party); party -1 when no marker.
ivec3 mech_decode_marker(vec4 texel) {
    ivec4 c = ivec4(round(texel * 255.0));
    if (c.a < 128 || c.b < 240) {
        return ivec3(0, 0, -1);
    }
    return ivec3(c.r, c.g, c.b - 240);
}

// Outline glow color of party 1..14 (spike/pack.tc has the same table).
vec3 mech_party_color(int party) {
    ivec3 c;
    if (party == 1) c = ivec3(230, 64, 64);
    else if (party == 2) c = ivec3(230, 135, 64);
    else if (party == 3) c = ivec3(230, 206, 64);
    else if (party == 4) c = ivec3(182, 230, 64);
    else if (party == 5) c = ivec3(111, 230, 64);
    else if (party == 6) c = ivec3(64, 230, 88);
    else if (party == 7) c = ivec3(64, 230, 159);
    else if (party == 8) c = ivec3(64, 230, 230);
    else if (party == 9) c = ivec3(64, 159, 230);
    else if (party == 10) c = ivec3(64, 88, 230);
    else if (party == 11) c = ivec3(111, 64, 230);
    else if (party == 12) c = ivec3(182, 64, 230);
    else if (party == 13) c = ivec3(230, 64, 206);
    else c = ivec3(230, 64, 135);
    return vec3(c) / 255.0;
}

#endif
