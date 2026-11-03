#version 330
#extension GL_ARB_separate_shader_objects : require

// Vanilla 26.3 core/text.vsh plus marked UI glyphs (mech:ui.glsl):
//   GUI (IS_GUI): HUD glyphs in a boss bar title move to a canvas anchor,
//     sized by window height, so GUI scale does not change them.
//   World: panel and cursor glyphs on text displays at the camera are placed
//     on the canvas directly, ignoring camera rotation and FOV. The cursor
//     follows the camera look direction. World glyphs (the gun reticle) stay
//     where they are, drawn smooth, full bright and without fog or shadow.
// Unmarked text renders exactly as vanilla.

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
#include <minecraft:fog.glsl>
#include <minecraft:sample_lightmap.glsl>
#endif

#include <minecraft:globals.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <mech:ui.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
layout(location = 3) in ivec2 UV2;
#endif

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
uniform sampler2D Sampler2;
layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
#endif

layout(location = 2) out vec4 vertexColor;
layout(location = 3) out vec2 texCoord0;
// 1 for marked UI glyphs: text.fsh samples them filtered (high-res art).
layout(location = 4) out float uiSmooth;

// All four corners at one point outside the screen: the quad is not drawn.
const vec4 HIDDEN = vec4(2.0, 2.0, 2.0, 1.0);
// Distance in front of the camera that panels are drawn at (near plane 0.05).
const float PANEL_DEPTH = 0.1;
// Layers, added to PANEL_DEPTH: panels use their z offset in -0.03..1
// (smaller is in front); the cursor is always in front of every panel.
const float CURSOR_LAYER = -0.04;

// Canvas position to whole window pixels.
vec2 canvas_to_pixels(vec2 canvasPos) {
    return floor(canvasPos * (ScreenSize.y / MECH_CANVAS_H) + 0.5);
}

#ifdef IS_GUI
// Boss bar n's title is drawn centered on GUI (guiWidth / 2, 3 + 19n)
// (BossHealthOverlay). Keep the glyph's offset from that point and move the
// point to the anchor; GUI units are converted back through ProjMat.
vec4 hud_position(vec4 viewPos, int data) {
    int anchor = data / 3;
    int slot = data % 3;
    float guiWidth = 2.0 / ProjMat[0][0];
    vec2 local = viewPos.xy - vec2(floor(guiWidth * 0.5), 3.0 + 19.0 * float(slot));
    vec2 canvas = mech_canvas_size(ScreenSize);
    vec2 pixels = canvas_to_pixels(mech_anchor(anchor, canvas) + local);
    viewPos.xy = pixels * (guiWidth / ScreenSize.x);
    return ProjMat * viewPos;
}
#else
// Canvas position straight to clip space. Up and depth come from ProjMat, so
// this holds for either clip-space convention and either depth range.
vec4 panel_position(vec2 canvasPos, float layer) {
    vec2 ndc = canvas_to_pixels(canvasPos) / ScreenSize * 2.0 - 1.0;
    vec4 up = ProjMat * vec4(0.0, 1.0, -1.0, 1.0);
    ndc.y *= -sign(up.y / up.w);  // canvas y runs down the screen
    vec4 front = ProjMat * vec4(0.0, 0.0, -(PANEL_DEPTH + layer), 1.0);
    return vec4(ndc, front.z / front.w, 1.0);
}
#endif

void main() {
    vec4 viewPos = ModelViewMat * vec4(Position, 1.0);
    gl_Position = ProjMat * viewPos;
    vec4 color = Color;
    bool marked = false;
    ivec4 mark = mech_decode(Color);

#ifdef IS_GUI
    if (mark.x == MECH_HUD) {
        marked = true;
        if (mark.w == 1) {
            gl_Position = HIDDEN;
        } else {
            gl_Position = hud_position(viewPos, mark.y);
            color = vec4(mech_palette(mark.z), Color.a);
        }
    }
#else
    if (mark.x == MECH_WORLD) {
        if (mark.w == 1) {
            gl_Position = HIDDEN;
        } else {
            marked = true;
            color = vec4(mech_palette(mark.z), Color.a);
        }
    } else if (mark.x == MECH_PANEL || mark.x == MECH_CURSOR) {
        // Menu displays sit at the camera (yaw 0, pitch 0, fixed billboard), so
        // Position is the glyph's offset from the display origin, in blocks.
        bool near = length(Position) < MECH_PANEL_RADIUS;
        if (mark.w == 1) {
            if (near) {
                gl_Position = HIDDEN;
            }
        } else if (!near) {
            gl_Position = HIDDEN;  // another player's menu
        } else {
            marked = true;
            vec2 canvas = mech_canvas_size(ScreenSize);
            vec2 local = vec2(Position.x, -Position.y) * MECH_TEXT_PX_PER_BLOCK;
            bool cursor = mark.x == MECH_CURSOR;
            vec2 origin = cursor
                ? mech_cursor_point(mech_look_degrees(ModelViewMat), canvas)
                : mech_anchor(mark.y, canvas);
            float layer = cursor ? CURSOR_LAYER : clamp(Position.z, -0.03, 1.0);
            gl_Position = panel_position(origin + local, layer);
            color = vec4(mech_palette(mark.z), Color.a);
        }
    }
#endif

#if !defined(IS_GUI) && !defined(IS_SEE_THROUGH)
    sphericalVertexDistance = marked ? 0.0 : fog_spherical_distance(Position);
    cylindricalVertexDistance = marked ? 0.0 : fog_cylindrical_distance(Position);
    vertexColor = marked ? color : Color * sample_lightmap(Sampler2, UV2);
#else
    vertexColor = color;
#endif
    texCoord0 = UV0;
    uiSmooth = marked ? 1.0 : 0.0;
}
