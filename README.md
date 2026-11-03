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
placeholder hull box, `@cpu` gauge). Next: the Stage 1 spikes in
[PLAN.md](PLAN.md).

| Path | Contents |
| --- | --- |
| `core/state.tc` | Mech and world state declarations + tunables |
| `core/loop.tc` | Main loop: per-tick drive, push-out, draw |
| `core/commands.tc` | `@mech @sit @clear @cpu @floor @help`, boarding |
| `mech/chassis.tc` | Spawn, drive, push-out, draw the chassis |
| `combat/ game/ ui/ maps/` | Empty until their stages |
| `pack/ tools/` | Resource pack source and build script (Stage 1) |
| `references/` | Mech, weapon and UI art, controls, augments, movement videos |
