# tc-dueling_game

A DiamondFire project written in [Terracotta](https://github.com/Owlfroggy/terracotta).

A legged-mech PvP game: pick a walker, sprinter, crawler or spider, fit it
from prebuilt parts, and drop with your party (1–5) onto one large map shared
by every party, for free-for-all fights or extraction raids. Models, sounds,
UI and screen effects come from a custom resource pack (core shaders and post
effects included). See [PLAN.md](PLAN.md) for the staged
plan and locked design decisions.

## Status

Pre-M1, Stage 0 done: a bare kinematic chassis (seat + `rideEntity` driving,
class skeletons of placeholder parts, `@cpu` gauge). Next: the Stage 1 spikes in
[PLAN.md](PLAN.md).

| Path | Contents |
| --- | --- |
| `core/state.tc` | Mech and world state declarations + tunables |
| `core/loop.tc` | Main loop: per-tick drive, push-out, draw |
| `core/input.tc` | Click and scroll events, routed by what the player is doing |
| `core/commands.tc` | `@mech @loadout @sit @clear @cpu @floor @parts @hitbox @hit @hp @splash @party @data @selftest @help`, the pack spike commands, boarding |
| `mech/chassis.tc` | Spawn a mech from a loadout, drive, push-out, draw |
| `mech/skeleton.tc` | Class skeletons: placeholder part displays, right-handed part matrices, two-bone knee solve |
| `mech/catalog.tc` | Part catalog: one row per prebuilt part (classes, guns, armor, augments, cosmetics), `@parts` |
| `mech/loadout.tc` | Loadouts: validation, defaults, derived stats, `@loadout` |
| `spike/cpu.tc`, `spike/pack.tc` | Stage 1 spikes: CPU test rigs (`@spike`), pack tests (`@pack @hud @menu @model @beep @fx @outline`); removed by MEC-23 |
| `combat/damage.tc` | `applyHit` damage funnel: armor reduction, part HP, splash, impulses; `@hp @splash` |
| `combat/loss.tc` | Part-loss effects per class (mobility, guns, torso lock, augments) and debris |
| `combat/destroy.tc` | Mech destruction: wreck effect, all parts to debris, seat removed, pilot handed to the mode |
| `combat/hitbox.tc` | Part hitboxes (boxes and leg capsules from the drawn displays), segment and splash queries, `@hitbox @hit` |
| `game/party.tc` | Parties of 1–5: invites (dialog or `@party`), accept, decline, leave, kick, leader, `allied` |
| `game/playerdata.tc` | Saved player data: one versioned record per player (loadout, credits, points, XP, unlocks, cosmetics, upgrade tiers, profile, settings), `@data` |
| `game/pack.tc` | Join flow: resource pack on join, loading title, decline handling, `packUrl()` of the published pack |
| `maps/` | Empty until its stage |
| `ui/markers.tc` | UI marker colors and run-time MiniMessage |
| `ui/hud.tc` | Combat HUD channels: panels of text items on boss bars, exact layout, send-on-change |
| `ui/schema.tc` | Damage schema and shield bar on the pilot's HUD |
| `ui/schemafont.tc` | Generated schema glyph table (`pack/src/schema_assets.py`) |
| `ui/fx.tc` | Screen effects per player through the glowing marker (zoom, shake, EMP, HRB, visor, low HP, death fade) |
| `ui/cockpit.tc` | Cockpit frame per class, weapon crosshair, gun reticle display |
| `ui/cockpitfont.tc` | Generated cockpit glyph table (`pack/src/cockpit_assets.py`) |
| `ui/private.tc` | Entities only their owner sees (markers, reticles), hidden from late joiners |
| `ui/menu.tc` | Menu framework: seated screens of panels, labels and buttons, hover, click, back, scroll |
| `ui/mainscreen.tc` | Main menu screen: top bar, map selector, play, customize, party panel |
| `ui/preview.tc` | 3D mech previews in menus (screen-locked by `core/item.vsh`) |
| `ui/settings.tc` | Settings screen: screen effects, screen shake, cursor speed; filters the effect marker |
| `ui/customizer.tc` | Robot customizer: categories, part options, stats, 3D mech; saves the loadout |
| `ui/hudfont.tc` | Generated HUD font advances (`pack/src/hud_assets.py`) |
| `pack/` | Resource pack source (`pack.mcmeta`, `assets/`; `src/` for Blockbench files and asset generators, not shipped) |
| `pack/assets/minecraft/shaders/core/text.vsh`, `pack/assets/mech/shaders/include/ui.glsl` | Text shader: HUD glyphs, screen-locked menu panels, cursor (marker protocol in PLAN.md, UI and HUD) |
| `test/selftest.tc` | Automated self-test: runs on join (entering play mode) and `@selftest`, prints `MECHTEST` lines |
| `tools/read_selftest.sh` | Switch to play (or any command), wait for the self-test, print its result from the client log |
| `tools/build_pack.py` | Validate the pack, compile its shaders, build `build/mech-pack-<hash>.zip`, publish to `pack-dist` |
| `tools/shader_variants.json` | Define sets each overridden shader must compile under |
| `references/` | Mech, weapon and UI art, controls, augments, movement videos |

## Resource pack

```sh
python3 tools/build_pack.py --check            # validate only
python3 tools/build_pack.py                    # build build/mech-pack-<hash>.zip
python3 tools/build_pack.py --publish --push   # add it to the pack-dist branch and push
```

Shader checks need `glslc` (shaderc) and a Minecraft 26.3 client jar
(found in the usual launcher folders, or pass `--vanilla <jar>` / set
`MC_VANILLA`). Published packs load from
`https://raw.githubusercontent.com/HarryLarrious/tc-mech_game/pack-dist/<file>`;
`latest.json` on that branch names the newest one.
