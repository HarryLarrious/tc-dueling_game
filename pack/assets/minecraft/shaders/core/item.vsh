#version 330
#extension GL_ARB_separate_shader_objects : require

// Vanilla 26.3 core/item.vsh, plus: items drawn in the world (perspective
// projection: mech parts on item displays) skip vanilla's per-vertex light
// and hand item.fsh their normal and view vector for per-pixel lighting.
// GUI items (orthographic projection) are lit exactly as vanilla.
// Menu previews (tint color with the low 2 bits of red, green and blue all
// set, MEC-103) are locked to the screen: no camera rotation, a fixed
// 70-degree projection, no fog. They sit in front of a seated menu player
// facing yaw 0, so world +z is straight ahead and world +x is to the left.

#include <minecraft:globals.glsl>
#include <minecraft:light.glsl>
#include <minecraft:fog.glsl>
#include <minecraft:dynamictransforms.glsl>
#include <minecraft:projection.glsl>
#include <minecraft:sample_lightmap.glsl>

layout(location = 0) in vec3 Position;
layout(location = 1) in vec4 Color;
layout(location = 2) in vec2 UV0;
layout(location = 3) in ivec2 UV1;
layout(location = 4) in ivec2 UV2;
#ifdef GLINT_SPECIAL
layout(location = 5) in vec2 UV3;
#endif
layout(location = 6) in vec3 Normal;

#ifndef OIT_ALPHA_ONLY
uniform sampler2D Sampler1;
uniform sampler2D Sampler2;

layout(location = 0) out float sphericalVertexDistance;
layout(location = 1) out float cylindricalVertexDistance;
#endif
layout(location = 2) out vec4 vertexColor;
#ifndef OIT_ALPHA_ONLY
layout(location = 3) out vec4 lightMapColor;
layout(location = 4) out vec4 overlayColor;
#endif

layout(location = 5) out vec2 texCoord0;
#ifdef GLINT
layout(location = 6) out vec2 texCoordGlint;
#endif
// World items only (inWorld = 1): world-space normal, and the camera-relative
// position for the view vector.
layout(location = 7) out float inWorld;
layout(location = 8) out vec3 worldNormal;
layout(location = 9) out vec3 cameraOffset;

// Vertical half-angle of the preview projection: tan(35 degrees).
const float PREVIEW_TAN = 0.7002;

bool is_preview(vec4 color) {
    ivec3 c = ivec3(round(color.rgb * 255.0));
    return (c.r & 3) == 3 && (c.g & 3) == 3 && (c.b & 3) == 3;
}

// Camera-relative position to clip space, ignoring camera rotation and the
// player's FOV, bobbing and tilt. x and y keep their perspective; depth is
// squeezed to 0.075..0.095 blocks so previews draw in front of every menu
// panel (0.07 and up) and behind the cursor (0.06). Depth comes from
// ProjMat's depth terms, so it holds for either depth convention.
vec4 preview_position(vec3 pos) {
    vec4 view = vec4(-pos.x, pos.y, -pos.z, 1.0);
    float aspect = ScreenSize.x / ScreenSize.y;
    mat4 proj = mat4(0.0);
    proj[0][0] = 1.0 / (PREVIEW_TAN * aspect);
    proj[1][1] = sign(ProjMat[1][1]) / PREVIEW_TAN;
    proj[2][2] = ProjMat[2][2];
    proj[2][3] = ProjMat[2][3];
    proj[3][2] = ProjMat[3][2];
    vec4 clip = proj * view;
    float near = 0.075 + 0.002 * clamp(-view.z, 0.0, 10.0);
    vec4 squeezed = ProjMat * vec4(0.0, 0.0, -near, 1.0);
    return vec4(clip.xy, squeezed.z / squeezed.w * clip.w, clip.w);
}

void main() {
    bool preview = ProjMat[3][3] < 0.5 && is_preview(Color);
    gl_Position = preview ? preview_position(Position) : ProjMat * ModelViewMat * vec4(Position, 1.0);

    #ifndef OIT_ALPHA_ONLY
    sphericalVertexDistance = preview ? 0.0 : fog_spherical_distance(Position);
    cylindricalVertexDistance = preview ? 0.0 : fog_cylindrical_distance(Position);
    #endif
    // A perspective projection has ProjMat[3][3] = 0, an orthographic one 1.
    inWorld = ProjMat[3][3] < 0.5 ? 1.0 : 0.0;
    worldNormal = Normal;
    cameraOffset = Position;
    vertexColor = inWorld > 0.5 ? Color : minecraft_mix_light(Light0_Direction, Light1_Direction, Normal, Color);
    #ifndef OIT_ALPHA_ONLY
    lightMapColor = sample_lightmap(Sampler2, UV2);
    overlayColor = texelFetch(Sampler1, UV1, 0);
    #endif

    texCoord0 = UV0;
    #ifdef GLINT
    #ifdef GLINT_SPECIAL
    texCoordGlint = (TextureMat * vec4(UV3, 0.0, 1.0)).xy;
    #else
    texCoordGlint = (TextureMat * vec4(UV0, 0.0, 1.0)).xy;
    #endif
    #endif
}
