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
| `core/commands.tc` | `@mech @loadout @sit @clear @cpu @floor @parts @help`, the pack spike commands, boarding |
| `mech/chassis.tc` | Spawn a mech from a loadout, drive, push-out, draw |
| `mech/skeleton.tc` | Class skeletons: placeholder part displays, right-handed part matrices, two-bone knee solve |
| `mech/catalog.tc` | Part catalog: one row per prebuilt part (classes, guns, armor, augments, cosmetics), `@parts` |
| `mech/loadout.tc` | Loadouts: validation, defaults, derived stats, `@loadout` |
| `spike/cpu.tc`, `spike/pack.tc` | Stage 1 spikes: CPU test rigs (`@spike`), pack tests (`@pack @hud @menu @model @beep @fx @outline`); removed by MEC-23 |
| `combat/ game/ ui/ maps/` | Empty until their stages |
| `pack/` | Resource pack source (`pack.mcmeta`, `assets/`; `src/` for Blockbench files and asset generators, not shipped) |
| `pack/assets/minecraft/shaders/core/text.vsh`, `pack/assets/mech/shaders/include/ui.glsl` | Text shader: HUD glyphs, screen-locked menu panels, cursor (marker protocol in PLAN.md, UI and HUD) |
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
