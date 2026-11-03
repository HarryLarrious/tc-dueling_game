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
| `core/commands.tc` | `@mech @loadout @sit @clear @cpu @floor @parts @hitbox @hit @hp @splash @selftest @help`, the pack spike commands, boarding |
| `mech/chassis.tc` | Spawn a mech from a loadout, drive, push-out, draw |
| `mech/skeleton.tc` | Class skeletons: placeholder part displays, right-handed part matrices, two-bone knee solve |
| `mech/catalog.tc` | Part catalog: one row per prebuilt part (classes, guns, armor, augments, cosmetics), `@parts` |
| `mech/loadout.tc` | Loadouts: validation, defaults, derived stats, `@loadout` |
| `spike/cpu.tc`, `spike/pack.tc` | Stage 1 spikes: CPU test rigs (`@spike`), pack tests (`@pack @hud @menu @model @beep @fx @outline`); removed by MEC-23 |
| `combat/damage.tc` | `applyHit` damage funnel: armor reduction, part HP, splash, impulses; `@hp @splash` |
| `combat/loss.tc` | Part-loss effects per class (mobility, guns, torso lock, augments) and debris |
| `combat/destroy.tc` | Mech destruction: wreck effect, all parts to debris, seat removed, pilot handed to the mode |
| `combat/hitbox.tc` | Part hitboxes (boxes and leg capsules from the drawn displays), segment and splash queries, `@hitbox @hit` |
| `game/ maps/` | Empty until their stages |
| `ui/markers.tc` | UI marker colors and run-time MiniMessage |
| `ui/hud.tc` | Combat HUD channels: panels of text items on boss bars, exact layout, send-on-change |
| `ui/schema.tc` | Damage schema and shield bar on the pilot's HUD |
| `ui/schemafont.tc` | Generated schema glyph table (`pack/src/schema_assets.py`) |
| `ui/fx.tc` | Screen effects per player through the glowing marker (zoom, shake, EMP, HRB, visor, low HP, death fade) |
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
