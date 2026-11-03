#ifndef MECH_UI_GLSL
#define MECH_UI_GLSL

// Marked UI glyphs carry their data in the text color (PLAN.md, UI and HUD):
//   red   = kind: 252 HUD glyph (boss bar title), 248 screen-locked panel, 244 cursor
//   green = 128 + 4 * a   HUD: anchor * 3 + bar slot; panel: anchor; cursor: 0
//   blue  = 128 + 4 * c   palette index
// a and c are 0..30. Vanilla draws a text shadow in color * 0.25 (floored), so a
// shadow copy reads red 63 / 62 / 61, green 32 + a, blue 32 + c.

const int MECH_NONE = 0;
const int MECH_HUD = 1;
const int MECH_PANEL = 2;
const int MECH_CURSOR = 3;

// Virtual canvas: always 360 units tall, as wide as the window's aspect.
// One canvas unit is one font pixel.
const float MECH_CANVAS_H = 360.0;
// Cursor travel: canvas units per degree of yaw/pitch away from yaw 0, pitch 0.
const float MECH_CURSOR_PER_DEG = 4.0;
// Text display font pixels per block (DisplayRenderer scales text by 0.025).
const float MECH_TEXT_PX_PER_BLOCK = 40.0;
// Marked world glyphs further than this from the camera are someone else's menu.
const float MECH_PANEL_RADIUS = 12.0;

// Returns (kind, a, c, isShadow); kind MECH_NONE for unmarked text.
ivec4 mech_decode(vec4 color) {
    ivec3 rgb = ivec3(round(color.rgb * 255.0));
    int kind = rgb.r == 252 ? MECH_HUD : rgb.r == 248 ? MECH_PANEL : rgb.r == 244 ? MECH_CURSOR : MECH_NONE;
    if (kind != MECH_NONE) {
        ivec2 d = rgb.gb - 128;
        if (d.x >= 0 && d.y >= 0 && d.x <= 120 && d.y <= 120 && d.x % 4 == 0 && d.y % 4 == 0) {
            return ivec4(kind, d / 4, 0);
        }
        return ivec4(MECH_NONE);
    }
    kind = rgb.r == 63 ? MECH_HUD : rgb.r == 62 ? MECH_PANEL : rgb.r == 61 ? MECH_CURSOR : MECH_NONE;
    if (kind != MECH_NONE) {
        ivec2 d = rgb.gb - 32;
        if (d.x >= 0 && d.y >= 0 && d.x <= 30 && d.y <= 30) {
            return ivec4(kind, d, 1);
        }
    }
    return ivec4(MECH_NONE);
}

vec3 mech_palette(int index) {
    if (index == 1) return vec3(0.62);              // grey
    if (index == 2) return vec3(0.30);              // dark grey
    if (index == 3) return vec3(0.47, 0.86, 1.00);  // cyan accent
    if (index == 4) return vec3(1.00, 0.72, 0.20);  // amber warning
    if (index == 5) return vec3(1.00, 0.30, 0.25);  // red danger
    if (index == 6) return vec3(0.45, 1.00, 0.45);  // green ok
    return vec3(1.0);                               // 0 and unused: white
}

vec2 mech_canvas_size(vec2 screenSize) {
    return vec2(MECH_CANVAS_H * screenSize.x / screenSize.y, MECH_CANVAS_H);
}

// Anchors 0..8 in reading order: 0 top-left, 4 center, 8 bottom-right.
vec2 mech_anchor(int anchor, vec2 canvas) {
    return vec2(anchor % 3, anchor / 3) * 0.5 * canvas;
}

// Camera yaw and pitch in degrees (Minecraft convention: yaw 0 looks +Z,
// pitch > 0 looks down). ModelViewMat is the inverse camera rotation, so its
// third row is the camera's backward axis in world space.
vec2 mech_look_degrees(mat4 modelView) {
    vec3 forward = -vec3(modelView[0][2], modelView[1][2], modelView[2][2]);
    return degrees(vec2(atan(-forward.x, forward.z), asin(clamp(-forward.y, -1.0, 1.0))));
}

// Where the cursor sits on the canvas; the server uses the same mapping.
vec2 mech_cursor_point(vec2 lookDegrees, vec2 canvas) {
    return clamp(canvas * 0.5 + lookDegrees * MECH_CURSOR_PER_DEG, vec2(0.0), canvas);
}

#endif
