#version 330
#extension GL_ARB_separate_shader_objects : require

// Vanilla 26.3 core/rendertype_outline.vsh, plus: the screen-effect marker
// (glow color blue >= 240, mech:fx.glsl) is drawn as a MECH_MARKER_SIZE
// square at the corner NDC (-1, -1) of the outline image, wherever the
// display is, so post_effect/entity_outline.json can read it at texel (0, 0).

#include <minecraft:globals.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <mech:fx.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;

layout(location = 0) out vec4 vertexColor;
layout(location = 1) out vec2 texCoord0;

void main() {
    gl_Position = ProjMat * ModelViewMat * vec4(Position, 1.0);

    if (mech_is_marker(Color.rgb)) {
        // Every quad of the marker model becomes the same small square;
        // its four vertices arrive in order, so the index picks the corner.
        int corner = gl_VertexIndex % 4;
        vec2 c = vec2(corner == 2 || corner == 3 ? 1.0 : 0.0, corner == 1 || corner == 2 ? 1.0 : 0.0);
        vec2 ndc = -1.0 + c * (2.0 * float(MECH_MARKER_SIZE) / ScreenSize);
        gl_Position = vec4(ndc, 0.0, 1.0);
    }

    vertexColor = Color;
    texCoord0 = UV0;
}
