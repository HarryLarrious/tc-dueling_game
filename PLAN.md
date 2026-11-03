# tc-dueling_game — Mech Battlefield Plan

Legged-mech PvP in Terracotta/DiamondFire. Pick a mech class, fit it from
prebuilt parts, and drop with your party (1–5 players) onto one large map
shared by every party. Two modes: **FFA**, where you fight with nothing at
stake, and **Extraction**, where you hunt other parties for upgrade points and
must get out alive to keep them. The feel mixes *86* (Juggernaut spider tanks,
Legion crawlers), *Titanfall* (fast, first-person cockpit combat) and
Arc Raiders-style extraction maps with mixed party sizes.

Repo: /home/harrylarrious/Projects/Repositories/tc-dueling_game

References in [references/](references/): mech art per class (including an
in-game walker build), weapon art, UI mockups and style references, three
Cymaera procedural-animation videos (the movement model), the control scheme,
and the augment list.

## Revisions 2026-11-02 — what changed

| Was | Now |
| --- | --- |
| 1v1 duel vs AI | One large shared map, parties of 1–5; FFA and Extraction modes |
| Freeform snap-together building | Prebuilt parts in fixed slots per class |
| Treads first, legs later | Legs only: 2-, 4- and 6-legged classes |
| Voxel cubes merged into block displays | Resource-pack models on item displays |
| Flat circular arena, no terrain | A large map with terrain, cover and climbable walls |
| Part-agnostic integrity counters | Per-part HP and hitboxes: shoot a gun or a leg off |
| Hitscan weapons | Projectiles with travel time: you lead your shots |
| Action-bar text readouts | Shader-placed HUD and mouse-driven menus |
| Server draws everything | Pack, core shaders and post effects do the purely visual work |

Kept: the math-not-simulation substrate, the single command dispatcher, the
guarded process loop, seat + `rideEntity` pilot input, the matrix-draw
pattern, the `@cpu` gauge.

## Locked decisions

- **Legs only.** Every mech walks. No treads, wheels or hover.
- **Prebuilt parts.** A mech is a class plus one prebuilt part per slot: main
  gun, secondary gun, armor, two augments (see Parts and loadouts). No
  freeform building.
- **Models come from a resource pack.** Every visible part is one item display
  showing a pack model (`setModel`). Skins, damage states and paint use custom
  model data strings and colors. The pack is sent on join with
  `sendResourcePack`; the game requires it (`isUsingResourcePack` gates
  queueing).
- **Physics is procedural, not simulated.** A rigid chassis with inertia plus
  procedurally animated legs (step rules + analytic IK). Heavy enough to feel
  good, cheap enough to run: O(legs) math per mech per tick, no solver.
- **Damage is per part.** Every part has HP and a hitbox. Losing a part loses
  its function: a gun shot off can't fire, a leg shot off changes how you move.
- **One shared map, parties of 1–5.** Every party in a session is on the same
  map; party sizes mix freely. Modes: FFA and Extraction.
- **Every gun fires projectiles with travel time.** You lead moving targets.
  The only instant shots come from the Black Powder augment.
- **Currencies.** Upgrade points are earned only in Extraction and spent on
  part upgrades. Cosmetic credits are only bought, through DF plot products.
- **UI ignores FOV and GUI scale and takes mouse input.** A core shader in the
  pack draws it on a fixed virtual canvas (see UI and HUD).
- **The UI does not look like Minecraft.** UI art and fonts are high
  resolution and anti-aliased, sampled smooth by our shaders; no pixel art
  (see UI and HUD, Art quality). The world is built maps and may look like
  Minecraft (owner, 2026-11-02: "only UI elements need to look like not
  Minecraft").
- **The client does the visual work.** Anything purely visual runs on the
  client through the resource pack, core shaders and post effects (see
  Client-side tech). The server computes gameplay state and sends only
  changes.

## Substrate — math, not simulation

The node-beam soft-body engine was dropped: a few nodes + beams measured over
50% of plot CPU, and DF has no native rigid-body solver. A mech is state plus
math, `{pos, vel, hullYaw, torsoYaw, gunPitch, feet[], parts[]}`, advanced in
O(1) per leg per tick and drawn with `teleport` +
`setDisplayTransformationMatrix` + `setDisplayInterpolation` (pattern proven in
`mech.tc`). Projectiles are the same idea: `{pos, vel}` stepped per tick with
segment tests. Pilot input stays native: interaction-entity seat,
`rideEntity`, `steerForwardMovement`/`steerSidewaysMovement`. Terrain queries
are native too: `game.raycast` returns where a ray stops. (Terracotta
beta.10 doesn't expose DF's Raycast to Block, which would also give the
face; the face comes from the hit point instead, whose coordinate on the hit
face is a whole number.)

## Mech classes

| | Walker | Sprinter | Crawler | Spider |
| --- | --- | --- | --- | --- |
| Weight | Heavy | Light | Heavy | Light |
| Legs | 2, reverse knee | 2, reverse knee (walker rig) | 6 | 4 |
| Armor | Heavy | Light | Heavy | Little to none |
| Mobility | Slow | Fast | Slowest, best step height | Fast, most agile, climbs walls |
| Main gun | Heavy, long cooldown | Light/medium, short cooldown | Heavy, long cooldown | Light, medium or heavy |
| Space | Forward boost | Jump | Forward boost | Jump; detach from a wall |
| Profile | Tall | Medium, slim | Low and wide | Smallest |
| Signature | Fires over cover, fast torso twist | Speed, jumps | Keeps moving after leg loss | Wall climbing, ambush |
| Leg loss | 1 leg lost = immobile, still shoots | 1 leg lost = immobile | Slower per leg; 3 left = immobile | Below 4 can't climb; 2 left = immobile |
| Displays (placeholder now / final est.) | 10 / ~10 | 10 / ~10 | 18 / ~16 | 14 / ~11 |
| Art refs | `walkers/` + the in-game build (`Pasted image.png`) | Walker art, lighter | `crawlers/` | `spiders/` (86 Juggernaut) |

**Sprinters are lighter walkers.** Same skeleton, gait code and IK as the
walker, with their own models: thinner legs and a lighter, more aerodynamic
hull. Only the models and stats differ.

Walkers and crawlers share a role (tanky, slow, heavy guns) but differ in
shape and in how they fail. A walker stands tall, sees and shoots over cover
and twists its torso fast, but one lost leg pins it in place. A crawler is low,
turns its turret slowly, climbs higher steps and keeps walking after losing
legs. A spider's gun size trades against agility: a heavy gun slows it and its
climbing, a light gun keeps it at full speed.

## Parts and loadouts

Each class has a fixed skeleton. A loadout picks one prebuilt part per slot:

| Slot | Sets | Notes |
| --- | --- | --- |
| Type | Class, skeleton, legs, base stats | Walker / Sprinter / Crawler / Spider |
| Main gun | Primary weapon | Size limited by class (table above) |
| Secondary gun | Backup weapon for main-gun cooldowns | Any class |
| Armor | HP and damage reduction against mass | Heavier kit = slower |
| Augments ×2 | Abilities on F and Q | Two different augments |
| Cosmetics | Paint, skin, decals | Custom model data only, no stats |

- **Catalog**: one data row per part: id, slot, allowed classes, model key(s),
  HP, mass, hitbox shape + local transform, joint pivot, and stats (guns:
  damage, cooldown, projectile speed, gravity, spread, splash, recoil; armor:
  reduction, HP bonus; augments: cooldown, duration, radius).
  Built in `mech/catalog.tc` (MEC-31): `global partCatalog` maps part id to a
  flat dict row; `partOrder` keeps catalog order. Field names and units are
  in the file header (ticks, blocks, blocks per tick, degrees; gun size is
  `sizeClass`, hitbox is `shape`/`size`/`offset`/`pivot`). The class row is
  the hull part and carries the class's base movement stats and the main gun
  sizes it accepts. Read rows with `partNum`/`partStr`; `partAllows(id,
  class)` and `partsFor(slot, class)` apply the class rules. Bump
  `catalogVersion()` after editing the data so plots rebuild it. `@parts
  [slot] [class]` lists the catalog. First-pass numbers, balanced in play.
- **Derived stats** (speed, acceleration, turn and traverse rates, mass) are
  computed when a loadout changes, never per tick. In `mech/loadout.tc`
  (MEC-33): `mass` = sum of part masses; `load` = extra mass over the bare
  class ÷ class mass; speed, turn and traverse = class base ÷ (1 + 0.25·load);
  acceleration = class base ÷ (1 + 0.5·load); hull HP = class HP × (1 +
  armor HP bonus); damage reduction from the armor; a spider with a heavy
  main gun is 15% slower and climbs at 60% speed. Default loadouts take the
  lightest main gun the class allows and the first fit for every other
  slot; `validLoadout` refits any illegal or missing slot and keeps the two
  augments different. A mech stores its loadout, class, stats and hull size
  at spawn (`mLoadout`, `mClass`, `mStats`, `mSize`); the chassis
  integration (MEC-24) reads `mStats`.
- **Commands**: `@loadout` shows yours with its stats; `@loadout <slot|class>
  <id>` and `@loadout reset` edit it (saved per player); `@mech` spawns it,
  `@mech <class>` spawns that class's default loadout.
- **Upgrades**: each part has an upgrade tree, bought with upgrade points,
  that raises its stats inside a capped range.
- **Persistence**: loadouts, unlocks, upgrade points, cosmetic credits and
  level are `saved` per player UUID.

## Weapons

Every gun fires projectiles. References are in `references/weapons/`.

| Weapon | Slot | Size | Feel | Reference |
| --- | --- | --- | --- | --- |
| Railgun | Main | Heavy | Fastest slug, almost no drop, big hit and recoil, long cooldown | `railgun/` |
| Light machine gun | Main | Light | Rotary, high rate, spread, short cooldown | `light machine gun/` |
| Medium main gun | Main | Medium | No reference yet (e.g. autocannon) | — |
| .50 cal deck gun | Secondary | — | Single heavy rounds, medium speed | `secondary weapons/50cal/` |
| Grenade launcher | Secondary | — | Revolving magazine, slow arcing shells, splash | `secondary weapons/gernade launcher/` |
| Machine burst | Secondary | — | Remote-turret machine gun, burst fire | `secondary weapons/machine burst/` |

**Projectiles**

- State lists: position, velocity, owner mech, weapon, ticks left, display.
- Per tick: `pos += vel`, `vel.y -= gravity` (per weapon). The segment from the
  old to the new position is tested against terrain (`game.raycast` along the
  segment), Electrostatic Domes (segment vs sphere), and mechs (bounding
  sphere, then part hitboxes). The first hit wins.
- Shots leave the muzzle along the gun direction (torso yaw + gun pitch), not
  the camera, and do not inherit the mech's velocity.
- No lead indicator: leading is the skill. The weapon panel shows projectile
  speed.
- Visuals: large rounds (railgun, .50 cal, grenades) get a stretched display
  moved with interpolation; machine-gun rounds use particles, with a tracer
  display on every Nth round. Tracers and muzzle flashes are emissive (core
  shader).
- A cap of 60 live projectiles removes the oldest first.
- **Aim (hold right click)**: steadier gun, tighter spread, slower torso
  traverse, slower walking, and a post-effect digital zoom set per gun (about
  1.5× for light guns up to 3× for the railgun) with a scope frame.
- **Switch fire (shift)**: toggles which gun left click fires; use the
  secondary while the main gun cools down.

## Augments

Two augment slots per mech, on F and Q (list from `references/augment.txt`).
Each has a cooldown; an EMP disables them for a while.

| Augment | Effect | Implementation |
| --- | --- | --- |
| Black Powder | Your next two shots deal more damage and travel instantly | The next 2 shots use an instant ray test instead of a projectile |
| Electrostatic Dome | Shield generator: a static field detonates enemy projectiles before they reach you | A sphere at the mech for N seconds; enemy projectiles crossing into it explode harmlessly |
| HMP Unit | Throws a projector that creates a standing hologram clone of your mech | A thrown projectile; on landing spawns a static copy of your displays (no per-tick cost) with one hitbox; pops when shot or after N seconds |
| EMP Engine | Fires an EMP charge that disables enemy augments near its detonation | A projectile; on detonation sets an augment-disabled timer on mechs in the radius and pops domes and holograms there |
| HRB Cannon | Air strike of hypervelocity rods on the spot you look at | Server ray from the eye picks the spot; a visible warning marker for ~2 s, then heavy splash damage with falloff |
| Internal Repair Torch | Repairs all damaged parts by 10% over 15 seconds | Once per second, adds 10%/15 of max HP to each damaged part; destroyed parts stay destroyed |

## Physics and animation

The model is Cymaera's procedural robots (the three videos in
`references/mech movement video references.txt`): feet stay planted and step
when they fall behind, legs are solved by IK, the body sits on its feet.
Trimmed to what DF CPU can afford.

Per mech per tick:

1. **Intent.** W/S/A/D give a desired velocity in the hull frame; the
   pilot's look gives the aim direction.
2. **Chassis.** `vel` eases toward the desired velocity at the class
   acceleration (mass-scaled), with friction when idle; `pos += vel`. The hull
   turns toward the move direction at the class turn rate. Torso yaw and gun
   pitch turn toward the aim at the class traverse rate, inside the class arc,
   so guns lag the camera (two reticles: where you look, where the guns point).
3. **Terrain.** One probe down under the body (step up within the class step
   height, fall otherwise) and one along `vel` (blocked: slide along the face;
   spider: may attach). Feet probe once per step, not per tick.
4. **Gait.** Each foot has a planted world point and a rest point in the body
   frame. A foot steps when it is farther than its stride from its rest point,
   its gait group is due and the other group is planted. Stride grows with
   speed. Groups: bipeds left/right, spiders diagonal pairs, crawlers
   alternating tripods. A step is an arc over a few ticks to a target led by
   `vel`.
5. **Body pose.** Height = mean planted-foot height + ride height. Pitch and
   roll come from front/back and left/right foot height differences, bob from
   the step phase. All eased, so the body never jitters.
6. **Leg IK.** Analytic two-bone IK (law of cosines) from hip to foot, with a
   per-class knee direction (reverse knee for bipeds, knee up for spiders and
   crawlers). Outputs the two segment matrices; the joint points double as the
   leg hitboxes.
7. **Impulses.** Recoil, hits, splash and collisions add to `vel`, scaled by
   1/mass. Big ones set a short stagger (no input, aim kick). Mech-vs-mech
   push-out is split by mass ratio.
8. **Jump, boost, falls.** Light mechs jump: an upward impulse, gravity, legs
   tucked to their rest pose in the air, little air control. Heavy mechs
   boost: a forward burst along the hull on a cooldown; the gait takes long,
   fast strides. No ground under the body means gravity until landing, then
   the feet re-plant with a landing stagger scaled by fall height.

**Spider climbing.** Pushing into a face taller than the step height attaches
the spider. Its up vector becomes the face normal from the `game.raycast` hit
point; W/S move up and down the face, A/D along it, and the feet probe the
wall plane. At the top edge it climbs over onto the roof; space detaches.
Heavy guns climb slower.

**Not simulated, on purpose:** no rigid-body solver, toppling, ragdolls or
per-part physics. A part shot off becomes a debris display on a short
ballistic arc (~1 s), then is removed.

**CPU rules**

- Idle mechs (not moving or turning) skip gait and IK; only changed matrices
  are written.
- LOD: mechs far from every player update legs every 2–4 ticks with a matching
  interpolation duration.
- No per-foot-per-tick probes, no raycasts inside IK.
- Purely cosmetic motion (minigun barrel spin, radar sweeps, light pulses) is
  animated by core shaders on the client, never by server matrix writes.
- **Measured (CPU spike, 2026-11-02, Plot 206003)**: about 1% base, then
  ~1.5% per crawler-sized mech (16 displays with IK, every tick), about 0.09%
  per display. LOD halves a mech's cost. A projectile costs ~0.14% at 10
  mechs and grows with mech count (one sphere test per mech). A raycast costs
  ~0.05%. Mounting displays on a root instead of teleporting each saved only
  ~6%, so displays are teleported individually.
- **Caps from those numbers**: 20 mechs per map (four full parties) and 60
  live projectiles, about 35% CPU at full load with half the mechs on LOD;
  the rest is headroom for AI, augments, HUD and events. Display matrix
  writes dominate, so skipping unchanged parts is the main saving.

## Damage

- **Direct hits**: the first part hitbox a projectile segment crosses
  (capsules for leg segments from the IK joints, oriented boxes for hull,
  torso, guns and augment modules).
- **Splash** (grenades, HRB rods, explosions): every part whose center is in
  the radius takes damage scaled by distance.
- **Hitboxes are the displays** (`combat/hitbox.tc`, MEC-35). `placePart`
  records each part's joint and display matrix columns whenever it draws
  the part, so hitboxes match what players see and move with IK at no extra
  cost (unchanged mechs skip both). Kinds: 1 box centered on the joint (hull,
  torso, augment modules), 2 box from the joint forward (guns), 3 capsule
  from the joint along the segment, radius half its width (legs).
  `segmentHit(p0, p1, skipMech)` tests each mech's bounding sphere, then its
  parts (slab test for boxes, segment-segment distance for capsules), and
  returns the nearest `{mech, part, t}`; `partsInRadius(mech, at, r)` and
  `hitboxCenter` serve splash. Part roles (`mPartRole`): hull, torso, main,
  secondary, aug1, aug2, thigh<n>, shin<n>. `@hitbox [mech]` draws them with
  particles; `@hit` tests a ray from the eye.
- **One funnel**: `applyHit(mech, part, amount, impulse)`. Every damage source
  goes through it.
- **Layers**: armor damage reduction → part HP. There is no passive shield;
  shielding comes from the Electrostatic Dome, and the HUD shield bar shows
  dome charge.

| Part destroyed | Effect |
| --- | --- |
| Hull / cockpit | Mech destroyed (see Modes for what happens next) |
| Main or secondary gun | That gun can't fire; both gone = disarmed (can still move, ram, use augments) |
| Leg segment | Leg lost; gait drops that foot; class leg-loss rule applies |
| Torso / turret ring | Torso locks; aim only by turning the hull |
| Augment module | That augment is disabled |

- **Feedback**: the HUD damage schema, a hit marker that names the part hit,
  debris for lost parts, sparks and smoke on low-HP parts.

## Modes and map

- **Parties**: 1–5 players. Parties queue together and always fight on the
  same side; every other party is hostile. Mixed sizes share one map.
- **The map**: one large map built on the plot (300×300, shared with the menu
  room). It has insertion points spread around the edge, extraction zones,
  cover, tall flat walls for spiders, an AI-mech waypoint graph, and a
  top-down image + preview image in the pack (minimap, map selector). Parties
  join a session until the 20-mech cap is reached.
- **FFA**: drop in at any time, respawn after a short timer, leave whenever
  you like. Nothing is gained or lost; XP for level only.
- **Extraction** (a raid with a time limit):
  1. The party inserts together at an insertion point away from other
     parties.
  2. Destroying other parties' mechs earns upgrade points, carried by the
     pilot and shown on the HUD. AI mechs drop small amounts.
  3. Extraction zones open during the raid. Holding one for a few seconds
     (visible and loud to everyone nearby) extracts the party members on it
     and banks their carried points.
  4. A destroyed mech drops its carried points as salvage at the wreck that
     anyone can collect. The pilot spectates their party for the rest of the
     raid.
  5. When the timer ends, anyone not extracted loses their carried points.
  Only carried points are at stake: mechs, parts and upgrades are never lost.
- **AI mechs** use the same intent + aim inputs as players: pick a target,
  move along the waypoint graph, keep class range, lead their shots with error
  and reaction delay, retreat at low HP. Class habits: walkers hold range,
  sprinters flank, crawlers push, spiders climb and ambush. They roam
  Extraction as a PvE threat, fill FFA when few players are online, and run
  Training ground.
- **One session per mode at a time on the plot** (see Open questions on FFA
  sharing the big map).

## Controls (from `references/controls references.txt`)

| Input | DF source | In a match | In menus |
| --- | --- | --- | --- |
| Mouse | player rotation | Look; torso and guns follow | Cursor |
| W/A/S/D | `steerForwardMovement`, `steerSidewaysMovement`, `movementKeyChange` | Move | — |
| Space | `vehicleJump` / `pressedMovementKeys` | Light mechs jump (spider: detach from wall); heavy mechs boost forward | — |
| Right click (hold) | `rightClick`, `isUsingItem`, `stopUsingItem` | Aim | Back |
| Left click | `leftClick` | Shoot the selected gun | Select |
| Shift | `movementKeyChange`; cancel `dismount` | Switch fire: main ↔ secondary | — |
| F | `swapHands` (cancelled) | Augment 1 | — |
| Q | `dropItem` (cancelled) | Augment 2 | — |
| Middle click | `pickBlock` / `pickEntity` | Ping: the server casts the look ray and marks what it hits for your party | — |

The player always holds one control item:

- a blank model, so no first-person hand is drawn;
- a use duration, so holding right click registers as using it;
- raised block and entity interaction range (item attributes), so middle click
  reaches far blocks for pings.

Shift normally dismounts a rider; the `dismount` event is cancelled so the
pilot stays seated. Verify every row on an interaction-entity seat in the
controls spike.

## UI and HUD

Layouts follow the mockups in `references/ui references/`. They are rough and
can change. Style: menus are clean flat panels over a backdrop (Duelyst
reference); the combat HUD is a holographic cockpit with cyan line art,
translucent panels and a class cockpit frame (cockpit reference).

**Screens**

- **Top bar** on every menu: Profile or Back home, Settings, etc. on the left;
  Shop, cosmetic credits, upgrade points on the right.
- **Main**: map selector with preview, queue selector, robot customizer, party
  display (up to 5 party mechs in 3D).
- **Queue selector**: FFA, Extraction and Training ground cards.
- **Robot customizer**: categories (type, main gun, secondary gun, armor,
  augments, cosmetics), the options for the chosen category, a 3D mech
  preview.
- **Shop**: part upgrade tree (upgrade points), cosmetic shops (cosmetic
  credits, bought through `promptPurchase`), a viewer.
- **Profile**: banners, titles, …; title and level visibility toggles; the
  banner card with level and title.
- **Combat HUD**: you + party list (top left), minimap (bottom left),
  weapon-dependent crosshair + gun reticle (center), damage schema + dome bar
  (right), active gun with main and secondary cooldowns, weapon info, and
  augment F/Q cooldowns (bottom right). Extraction adds carried points, raid
  timer and extraction zone markers. Pings are world-space markers shown only
  to your party.

**How it is drawn**

- All UI art is font glyphs (PNG bitmaps) and models in the pack.
- **Art quality** for UI (owner, 2026-11-02: "high resolution and high
  quality, something that doesn't look like a Minecraft game", later
  narrowed to UI elements only):
  - Glyph art is drawn anti-aliased (rendered 4× and downsampled with
    premultiplied alpha) at about 4–8 texels per canvas unit: at 1440p one
    canvas unit is 4 screen pixels, at 4K 6.
  - A glyph image must be under 255 px a side: the font atlas pages are
    256×256 with 1 px spacing (`FontTexture`), and a glyph that does not fit
    becomes the missing-glyph box. Larger art is split into several glyphs
    laid side by side with spacing glyphs.
  - Every glyph keeps a 2 px transparent margin, so filtered sampling never
    reaches a neighbouring glyph in the atlas.
  - The font atlas sampler is `NEAREST`, so `core/text.fsh` samples marked
    glyphs itself: bilinear when magnified, a 4-tap footprint average when
    shrunk, on premultiplied colors (no dark fringes). Unmarked text samples
    as vanilla.
  - **UI text** (MEC-97): Rajdhani SemiBold (SIL OFL 1.1, license shipped as
    `assets/mech/font/rajdhani-ofl.txt`) in three TTF fonts, all
    `oversample` 4 (about 1:1 at 1440p):

    | Font | Size (canvas units) | Use |
    | --- | --- | --- |
    | `mech:text_s` | 7 | small labels, status words |
    | `mech:text` | 10 | readouts, menu labels |
    | `mech:text_l` | 16 | big numbers |

    TTF glyphs are grayscale, so they go through the `IS_GRAYSCALE` text
    variants and the shared filter reads them as `.rrrr`. Text only gets
    the smooth sampling and canvas placement when it carries a marker color.
    The plot's chat and other unmarked text keep Minecraft's font (MEC-98).
    Verified on Plot 206003 (2026-11-02): smooth at GUI scale 1–4, HUD
    readout (`@hud text`) and menu label (`@menu`) placed correctly.
  - Mech parts (MEC-19, optional now that only the UI must not look like
    Minecraft): textures at 16 texels per model unit, sampled filtered by
    `core/item.fsh` and lit per pixel (sky/ground ambient, a wrapped key
    light, specular and rim, times the lightmap). GUI items stay vanilla.
- A **core shader** recognizes marked UI elements and places them on one
  *virtual canvas* scaled to the window height. It cancels the GUI scale and
  uses its own fixed projection instead of the player's FOV, so size and
  position never change with either setting. The canvas is 360 units tall and
  as wide as the window's aspect (640 at 16:9); one unit is one font pixel.
- **Marker: the text color** (`core/text.vsh` + `mech:ui.glsl`, MEC-18):

  | Channel | Value |
  | --- | --- |
  | red | kind: `252` HUD glyph in a boss bar title, `248` screen-locked panel, `244` cursor |
  | green | `128 + 4·a`; HUD: `a = anchor·3 + bar slot` (slot 0–2); panel: `a = anchor`; cursor: `a = 0` |
  | blue | `128 + 4·c`; `c` = palette index (0 white, 1 grey, 2 dark grey, 3 cyan, 4 amber, 5 red, 6 green) |

  `a` and `c` are 0–30. Anchors 0–8 run in reading order (0 top-left,
  4 center, 8 bottom-right). The glyph is drawn in its palette color, not the
  marker color, at full brightness with no fog. Vanilla's text shadow is
  `color × 0.25`, so a marked glyph's shadow decodes too and the shader hides
  it. Side effect: on our plot, GUI text colored red ≥ 252 with green and
  blue in 128–251 loses its shadow; avoid those colors for normal text.
- **Building glyph text in DF**: text built at run time (computed marker
  colors) goes through "Parse MiniMessage Expression" with Allowed Tags
  **Full**; the default "Style Only" drops `<font:mech:ui>` and the glyphs
  show as missing-glyph boxes.
- **HUD glyphs**: send the glyph as a boss bar's title. Vanilla centers bar
  `n`'s title on GUI (width/2, 3 + 19n); the shader keeps each glyph's offset
  from that point and moves the point to the anchor. The string's center
  lands on the anchor; shift it with space glyphs. Only bar slots 0–2 can be
  addressed, and at high GUI scale vanilla stops drawing bars below a third
  of the screen height.
- **Menu displays** (panels and the cursor) are text displays placed exactly
  at the player's eye, yaw 0, pitch 0, billboard fixed, background alpha 0,
  no shadow, hidden from everyone else. The shader reads each glyph's offset
  from the display origin (40 canvas units per block, display scale 1) and
  adds the anchor. A display's translation moves it on the canvas; its z
  translation orders overlapping panels (smaller z is in front, −0.03 to 1);
  the cursor is always drawn in front of every panel.
  Marked glyphs further than 12 blocks from the camera are hidden, so a
  missed `setEntityHidden` never shows another player's menu.
- **Cursor mapping** (shader and server must match): with yaw normalized to
  −180..180 (0 looks +Z),
  `cursor = (W/2 + 4·yaw, 180 + 4·pitch)` in canvas units, clamped to the
  canvas. The menu seat faces yaw 0. Hover tests on the server use offsets
  from the canvas center (`4·yaw`, `4·pitch`), which do not depend on the
  window's aspect, so clickable panels use the center anchor (4).
- **Combat HUD on the GUI layer**: boss bars for persistent panels (party
  list, damage schema, weapon panel, minimap), title and action bar for
  transient ones. These are per player by nature and are resent only when a
  value changes (cooldowns quantized).
- **Menus in a menu room**: the player rides a fixed seat. Panels, a backdrop
  and 3D previews (party mechs, customizer mech, shop viewer) are text and
  item displays in front of the seat. The shader locks them to the screen
  (ignoring camera rotation) and projects them with the fixed projection.
  `setEntityHidden` hides each player's menu entities from everyone else
  (including late joiners), so all players can share one room.
  `setDisplayCullingSize` stops them from being culled.
- **Mouse cursor without lag**: moving the mouse turns the camera. The shader
  draws the cursor from the camera rotation, so it moves on the client at
  once. The server applies the same mapping to the player's yaw and pitch for
  hover and clicks, and `setRotation` holds the camera at the canvas edges.
- The pack hides vanilla HUD sprites (crosshair, hotbar, hearts, food, XP,
  boss bar bars) so only our HUD shows. Done so far: boss bars, the
  crosshair (combat draws its own) and the hotbar frame, selection and
  offhand slots.
- **No hand, no hotbar items**: the player holds one item with the empty
  model `mech:blank` (`"type": "minecraft:empty"`) in slot 1 and nothing
  else. With an item in the main hand vanilla does not draw the
  first-person arm, and the blank item draws nothing in hand or hotbar. Its
  name is a 1-pixel space glyph so the item-name popup stays empty.
- **Spacing glyphs** in `mech:ui`: U+F801/F802/F804/F808/F810/F820/F840 move
  −1/−2/−4/−8/−16/−32/−64 px, U+F821/F822/F824/F828/F830/F860/F880 move
  +1…+64 px. Following a glyph with minus its advance gives several glyphs
  one origin.
- Text entry (party invite by name, loadout names) uses DF dialogs.
- If your own cockpit shell blocks your first-person view, `setEntityHidden`
  hides it from the pilot only.

## Client-side tech: resource pack, core shaders, post effects

The server computes gameplay state and sends changes; everything purely
visual runs on the client. One pack carries all of it, so the CPU budget pays
only for gameplay.

| Need | Tool | How |
| --- | --- | --- |
| Mech, gun, projectile and debris models | Pack: models + item model definitions | `setModel`; damage states and skins select on custom model data strings, party colors tint from custom model data colors |
| UI art, map images, damage schema | Pack: font glyphs | Sent as text components |
| UI placement, cursor | Core shader: `text` | See UI and HUD |
| Gunfire, railgun charge, minigun spin-up, footsteps, servos, alarms | Pack: `sounds.json` + OGG files | DF custom sounds |
| Cockpit screens, hologram panels, muzzle flashes, dome field | Pack: animated textures (`.mcmeta`) | No server cost |
| Lights, visors and tracers that glow | Model `light_emission` or core shader: `item` | Static glow: the vanilla element field `light_emission: 15`, no shader. Shader glow: texture alpha 250 renders full bright and opaque, 251 the same plus a 1 Hz pulse on `GameTime` |
| Minigun spin, radar sweep, light pulse | Core shader: `item` | Marked vertices animated by game time |
| Electrostatic Dome bubble | Core shader: `item` | One billboarded display drawn as a sphere with a bright edge |
| 3D menu previews | Core shader: `item` | Screen-locked like the menu panels |
| Aim zoom, shake, damage and EMP effects, visor look | Post effects | See below |
| Party members outlined through walls | Glowing + outline core shader + post effect | See below |
| No vanilla HUD, crosshair or hand | Pack: transparent sprites, blank control-item model | — |

**Core shaders** replace vanilla vertex and fragment shaders. Ours change only
geometry that carries a marker (reserved vertex color or alpha values, picked
in the spike); everything else renders as vanilla.

**Target client: Minecraft 26.3, resource pack format 97.1.** What the 26.3
client gives us (decompiled source and shaders in the minecraft-source MCP):

- **Shader names.** 26.3 merged the old per-render-type shaders: `core/text`
  draws text displays and GUI text, `core/item` draws item displays (all mech
  parts), `core/entity` draws mobs, and `core/rendertype_outline` draws glow
  outlines. Variants are compile-time defines (`IS_GUI`, `IS_SEE_THROUGH`,
  `IS_GRAYSCALE`, `OIT_*`), so one edited file must compile under every
  define. Guides written for `rendertype_text` and older names don't apply.
- **Uniforms.** `Globals` (`ScreenSize`, `GameTime`, `CameraOffset`),
  `Projection` (`ProjMat`) and `DynamicTransforms` (`ModelViewMat`,
  `ColorModulator`) are bound for the text, item, entity and outline
  pipelines.
- **GUI scale.** GUI text uses an orthographic projection over window size
  divided by GUI scale, so the shader recovers the scale as
  `ProjMat[0][0] * ScreenSize.x / 2` and cancels it.
- **Camera.** In the world, vertex positions arrive camera-relative and
  `ModelViewMat` is the camera's view rotation only. Skipping it locks an
  element to the screen; its rows give the look direction for the cursor.
  `ProjMat` carries FOV, view bobbing and the damage tilt, so our fixed
  projection drops all three.
- **Culling.** A display with culling width or height 0 (the default) is
  never frustum-culled; only view range limits it.
- **Outline post hook.** The `entity_outline` chain runs when any outline is
  drawn that frame, and may read and write both `minecraft:entity_outline`
  and `minecraft:main`. Frame order: world → outline chain → first-person
  hand → outline blit → vanilla post effects → GUI. Our effects therefore
  touch the world but never the HUD. The chain must clear the marker pixel
  from the outline image so it doesn't show.
- **Item tint and light.** `core/item` multiplies the texture by the vertex
  color (custom model data tint) and the lightmap; skipping the lightmap for
  marked pixels makes them emissive. Normals and positions arrive in
  camera-relative world axes, so our world lighting is fixed in the world.
  World items are told apart from GUI items by the projection
  (`ProjMat[3][3]` is 0 for perspective, 1 for orthographic).
- **Improved transparency.** With that video option on, translucent text and
  items use order-independent-transparency variants (`OIT_*` defines); test
  the shaders with the option on and off.
- **Overrides.** The shader manager reloads `shaders/` and `post_effect/` from
  resource packs, so the pack replaces them directly.

**Post effects** are full-screen passes. Vanilla runs the `entity_outline`
post effect whenever a glowing entity is on screen, and the pack replaces it:

- Each player in a match has one tiny glowing marker display, hidden from
  everyone else with `setEntityHidden`. Its glow color
  (`setDisplayGlowColor`) carries the effect id, its strength and the player's
  party id. The outline core shader moves the marker to a fixed corner pixel,
  and the post passes read that pixel. Changing an effect costs one
  `setDisplayGlowColor` call; the animation runs on game time in the shader.
- Post effects run before the GUI is drawn, so the HUD never zooms, shakes or
  blurs.
- **Marker encoding** (MEC-20, `mech:fx.glsl`), the marker's glow color:

  | Channel | Value |
  | --- | --- |
  | red | effects bitmask: 1 zoom (up to 3×), 2 shake, 4 red damage tint with vignette, 8 desaturate |
  | green | strength 0–255 |
  | blue | `240 + party`: 0 shows every outline, 1–14 only that party's color, 15 none (solo players) |

  Glow colors with blue ≥ 240 are reserved for the marker.
- **Party outline colors** (party 1–14; every channel ≤ 230, so never a
  marker): `#E64040 #E68740 #E6CE40 #B6E640 #6FE640 #40E658 #40E69F #40E6E6
  #409FE6 #4058E6 #6F40E6 #B640E6 #E640CE #E64087`. A mech glows in its
  party's color; the filter keeps only the viewer's own party.
- **How it is drawn**: `core/rendertype_outline.vsh` turns every quad of the
  marker into a 2×2-pixel square at the outline image's NDC (−1, −1)
  corner, read back in post passes as texel (0, 0) on either backend.
  `post_effect/entity_outline.json` runs: `mech:post/fx` (main + outline →
  `fx`), blit `fx` → `minecraft:main`, `mech:post/outline_filter` (drops the
  marker and other parties' outlines), then vanilla's sobel, two blurs and
  blit. The marker display is an item display at scale 0.01 riding the
  player, hidden from the other players only (hiding it from its owner too
  and showing it again re-sends it and loses it).
- **Marker pitfalls found in game** (MEC-20):
  - Item outlines draw with back-face culling (`OUTLINE_CULL`). The marker
    square is wound counter-clockwise; clockwise was always culled.
  - Draws share one vertex buffer and may start at any vertex, so
    `gl_VertexIndex % 4` is only a corner index up to rotation. A fixed
    winding survives that; anything that changes per quad (e.g. alternating
    by `gl_VertexIndex / 4`) breaks quads apart.
  - Give the marker a real culling box (`setDisplayCullingSize(4, 3)`)
    instead of 0: vanilla inflates it by 0.5 so it contains the camera, and
    it stays visible to culling mods (Sodium, EntityCulling) in every view
    direction.

| Effect | When |
| --- | --- |
| Digital zoom + scope frame | Holding right click; zoom level per gun |
| Shake + flash | Big hits, railgun recoil, heavy landings, HRB impacts |
| Edge pulse | Low HP, or a part about to break |
| Static, glitch, color split | Hit by an EMP, while your augments are down |
| Red warning pulse | Standing in a marked HRB strike zone |
| Visor (scanlines, vignette) | Always on in the cockpit, subtle |
| Desaturate + fade | Mech destroyed, spectating |
| Party outlines | Always: every mech glows in its party-id color; the post pass keeps only outlines that match your party id |

Settings offer screen effects full / reduced / off and screen shake on / off;
the marker carries the choice.

**Pack source and hosting**

- Source in `pack/` (namespace `mech`: `items/`, `models/`, `textures/`,
  `font/`, `sounds/`; vanilla overrides under `minecraft/`: `shaders/core/`,
  `shaders/post/`, `post_effect/`, HUD sprites), Blockbench sources in
  `pack/src/` (not shipped). `pack.mcmeta` pins `min_format`/`max_format` to
  `[97, 1]`; shaders change between versions, so a new client version means a
  re-test and a new range.
- `tools/build_pack.py` validates and builds the pack:
  - JSON parses with no duplicate keys; every asset path is a valid resource
    location (the game skips bad names silently).
  - Every shader compiles with `glslc` the way the 26.3 client compiles it
    (shaderc, Vulkan 1.2, auto-bound uniforms, `#include <ns:path.glsl>` from
    `shaders/include/`) under every define set in
    `tools/shader_variants.json`: all subsets of the shader's flags × no OIT
    and each OIT stage × the device macros on and off. That superset passes
    on the vanilla shaders. An overridden `minecraft:core/*` shader without an
    entry fails the build. Vanilla includes are read from a local 26.3 client
    jar (`--vanilla` or `MC_VANILLA`); they are never committed.
  - The zip is deterministic and named `mech-pack-<content hash>.zip`.
- Hosted on the orphan `pack-dist` branch (built zips, `latest.json`, a
  README; nothing else) and loaded from
  `https://raw.githubusercontent.com/HarryLarrious/tc-mech_game/pack-dist/<file>`.
  `build_pack.py --publish` commits there without touching the work tree;
  `--push` pushes. DF's `sendResourcePack` takes only a URL (no hash), and
  raw files are cached for 5 minutes, so the content-hash file name is what
  makes clients fetch a changed pack. An unchanged pack keeps its name.
- Join flow: `sendResourcePack` → `resourcePackLoad` → menu room;
  `resourcePackDecline` → explain why the pack is needed, offer a retry.

**Model rules**

- Java item models are boxes inside the −16..32 range. In 26.3 an element
  rotates freely: `"rotation": {"origin": [...], "x": a, "y": b, "z": c}`
  (any angles, applied X then Y then Z), or the old single `axis` + `angle`.
  Large parts scale up through the display matrix. Each part's joint (hip,
  knee, shoulder, turret ring) sits at the model center (8, 8, 8), the display
  origin, so matrices rotate parts about their joint. An item display turns
  its model 180° about y before the display matrix (`DisplayRenderer`), so a
  part that extends from its joint along the mech's forward axis is modeled
  along model −z. Display matrices are right-handed (columns left, up,
  forward with left = up × forward): a mirrored matrix draws the model
  inside out. One model per part;
  damaged variants and skins select on custom model data strings, party color
  tints from custom model data colors.
- **Glow.** An element with `"light_emission": 15` (0–15) renders at full
  block light with no shader. Pixels for the item shader use alpha 250 (full
  bright) or 251 (full bright, pulsing). Any alpha other than 0 or 255 inside a face's UV area sends that
  whole face to the translucent item pipeline (`FaceBakery`), so marked pixels
  go on their own small faces and the rest of the part stays cutout.
- **Textures** may be high resolution (16 texels per model unit) and are
  sampled filtered, so keep UV islands at least 2 texels apart and 2 texels from the
  texture edge, with their edge colors extended into that gap: a filtered
  sample at a face edge then never picks up a neighbouring island or the
  next sprite in the atlas.
- Item model definitions live in `assets/mech/items/<part>.json`
  (`setModel(item, "mech:<part>")`); party color is a
  `minecraft:custom_model_data` tint (index 0) on faces with `tintindex: 0`.
- **Placeholders (MEC-32).** Until the art pass every part is one of two
  tinted box models: `mech:skel_box` (a unit box centered on its joint: hull,
  torso) and `mech:skel_segment` (a unit box from its joint along forward:
  guns, thighs, shins), scaled and pointed by the display matrix. Each class's
  skeleton (`mech/skeleton.tc`, `classSkeleton`) lists ride height, torso,
  gun mounts, hips, rest feet, bone lengths and the knee pole (backward for
  the reverse-knee bipeds, up for crawlers and spiders). Display order per
  mech: hull, torso, main gun, secondary gun, augment modules 1 and 2 (side
  pods on the hull flanks), then thigh and shin per leg.
  Legs hold a rest pose solved by `kneeOf` (two-bone IK) until gait moves
  the feet.
- Placeholder box models first, art pass later. The in-game walker build is
  the target look for the walker models.

## Plan — ordered least reliance / most important first

### Stage 0 — Reset (deps: none)
1. Remove the voxel layer: cube, part and cuboid lists in `state.tc`;
   `buildCuboids`, `sameCell`, `cellKey`, `addCube`, `addPartToMech`,
   `spawnTestMech` in `mech.tc`; their resets in `commands.tc`. Keep the loop,
   dispatcher, seat/ride, push-out and `@cpu`.
2. Folder skeleton: `core/`, `mech/`, `combat/`, `game/`, `ui/`, `maps/`,
   `pack/`, `tools/`. Compile clean with `tc-check.sh`.

### Stage 1 — Spikes: the biggest risks, before building on them (deps: 0)
3. **CPU spike**: a crawler-sized rig (16 item displays) running dummy gait +
   IK every tick, plus live projectiles with segment tests. Measure `@cpu`
   with 1, 5, 10, 15 and 20 rigs and with 25, 50 and 100 projectiles, with
   and without LOD. Output: cost per mech and per projectile → mech cap per
   map, projectile cap, LOD distances. **Done**: see CPU rules (20 mechs,
   60 projectiles).
4. **Pack + shader spike**: a minimal pack (one part model, one glyph, one
   sound, the core shaders, the outline post effect) sent with
   `sendResourcePack`. Prove on DF's client version:
   - a pack model on an item display, joint pivot correct; a custom sound;
   - an emissive pixel and a game-time animation on a marked model;
   - the glowing marker driving a post effect (zoom and shake) with the HUD
     unaffected, and the party-outline filter;
   - a marked boss-bar glyph at the same screen spot at GUI scale 1–4 and
     FOV 30–110;
   - a menu panel locked to the screen while the camera turns, hidden from a
     second player;
   - a shader cursor that follows the mouse with no lag and matches the
     server's hover mapping.

   Spike assets (MEC-17, generated by `pack/src/spike_assets.py`): item
   `mech:test_part` (joint housing centered on the display origin, a tinted
   arm rising from it, a reserved-alpha strip on its north face and a
   `light_emission` strip on its south face), font `mech:ui` (U+E000 panel
   64×32, U+E001 cursor 8×8 with its tip at the top-left), sound
   `mech:test.beep`, and transparent `boss_bar` sprites.

   Results on Plot 206003, 2026-11-02 (owner: "all works"), after the
   fixes found on the way: glyph MiniMessage needs Allowed Tags Full; the
   cursor needed its own depth layer; hotbar, hand and crosshair hidden;
   UI art redone high resolution with filtered sampling.

   Test commands (MEC-21, `spike/pack.tc`): `@pack [url|status|clear]`,
   `@hud [anchor] [palette] | grid | off`, `@menu`, `@model [party]`,
   `@beep`, `@fx <zoom+shake+tint+gray> [strength%] [party] | off`,
   `@outline [party party party]`. Results (fill in on
   the plot; ✅ pass, ❌ fail + note):

   | Check | Command | Result |
   | --- | --- | --- |
   | Pack downloads and loads (`resourcePackLoad` fires) | `@pack` | ✅ also sent on join |
   | Test part shows, tint follows the party color | `@model 1`…`5` | ✅ |
   | Joint stays still while the arm swings | `@model` | ✅ |
   | `light_emission` strip bright in the dark | `@model` at night | ✅ |
   | Custom sound plays | `@beep` | ✅ |
   | Boss bar shows only its title (sprites hidden, shadow hidden) | `@hud` | ✅ |
   | HUD glyphs keep their screen spot at GUI scale 1–4 | `@hud grid` | ✅ |
   | … and at FOV 30–110 | `@hud grid` | ✅ |
   | Menu panel locked while the camera turns | `@menu` | ✅ |
   | Cursor follows the mouse with no lag | `@menu` | ✅ drawn above the panel |
   | Server hover matches the visible cursor (panel turns cyan) | `@menu` | ✅ |
   | Menu hidden from a second player | `@menu` + 2nd player | — |
   | All of the above with improved transparency on | — | item glow ✅; UI not checked yet |
   | Emissive pixel and game-time animation | `@model` (MEC-19) | ✅ 250 glows, 251 pulses, also with improved transparency |
   | High-res part texture smooth, world lighting on parts | `@model` (MEC-19) | ✅ |
   | Marker glow drives zoom/shake, HUD unaffected | `@fx zoom+shake 60` | ✅ zoom, shake, tint, gray, any view direction |
   | Only the party color's outlines show | `@outline`, `@fx zoom 0 2` | ✅ |
5. **Controls spike**: on an interaction-entity seat, confirm every row of the
   controls table: cancelled `dismount` keeps the pilot seated and shift is
   still readable; space while riding; holding right click with the control
   item; middle click on a block 60+ blocks away; F and Q cancelled.

   **Gate**: anything that fails switches to its fallback (see risks) before
   Stage 2.

### Stage 2 — Walking chassis (deps: 1)
6. Chassis state and integration (vel, acceleration, turn rate, torso
   traverse and arc); piloting from the seat; aim from look.
7. Terrain probes: step up, fall, wall slide.
8. Gait + two-bone IK, biped first, then 4- and 6-leg gaits; body pose from
   the feet.
9. Jump (light) and boost (heavy); mech-vs-mech push-out by mass; impulses
   and stagger.

### Stage 3 — Classes and parts (deps: 2, models from 4)
10. Part catalog and the class skeletons with placeholder models (walker rig
    shared by sprinters); loadout data; derived stats; spawn a mech from a
    loadout.
11. Display LOD and skip-unchanged writes, tuned from the spike numbers.

### Stage 4 — Damage (deps: 3)
12. Hitboxes per part; armor and part HP; direct hits and splash through the
    `applyHit` funnel.
13. Part-loss effects per class; debris; mech destruction and cleanup.

### Stage 5 — Projectiles and guns (deps: 4)
14. Projectile lists, stepping, gravity, segment tests against terrain and
    part hitboxes, cap.
15. The six guns; main + secondary with switch fire; aim mode; recoil.
16. Tracers, impacts, sounds.

### Stage 6 — Spider climbing (deps: 2, 3)
17. Wall attach, move, climb-over, detach; gun-size penalty.

### Stage 7 — Augments (deps: 5)
18. The six augments on F and Q, cooldowns, EMP disable; their visuals (dome
    bubble, HMP clone, HRB marker).

### Stage 8 — Combat HUD and screen effects (deps: 4, 5, 7, spike 4)
19. Cockpit frame, crosshair + gun reticle, damage schema, dome bar, gun
    panel and cooldowns, augment cooldowns, party list, minimap, hit markers,
    killfeed, pings.
20. Post effects (zoom, shake, damage, EMP, HRB warning, visor, death), party
    outlines, and the effects settings.

### Stage 9 — AI mechs (deps: 5)
21. AI on the player input path; waypoint graph; leading with error;
    difficulty.

### Stage 10 — FFA (deps: 8, 9) — first fun checkpoint
22. The map and its metadata; parties on one side; drop-in, respawn, leave.
23. **Balance + CPU pass** at the mech cap with AI mechs firing.

### Stage 11 — Extraction (deps: 10)
24. Raid sessions: insertion, carried points, salvage, extraction zones, raid
    timer, spectating, banking and results.

### Stage 12 — Menus (deps: 3, spike 4)
25. Menu room, cursor, top bar, main screen, queue selector, robot customizer
    with 3D preview, settings.
26. Parties (invite, party display, queue together) and the queues.

### Stage 13 — Progression and store (deps: 11, 12)
27. Saved player data; upgrade trees; cosmetic store through plot products
    (`promptPurchase`, `purchaseProduct`, `ownsProduct`); profile (banners,
    titles, level, toggles).

### Stage 14 — Content and polish (deps: 11)
28. More maps, parts and augments, model and sound art pass, more emissive
    and animated detail, death explosions, drop-in, README.

## Milestones (each must compile clean AND playtest in-game before the next)

- **M1** (S0+S1): spikes pass — measured mech and projectile budgets; the
  shader UI, post effects and every control working on DF.
- **M2** (S2): one walker walks over terrain on planted feet, piloted.
- **M3** (S3–S6): all four classes, per-part damage, projectile guns — you
  can lead a shot and take an enemy's gun off.
- **M4** (S7–S10): augments, combat HUD, AI mechs, FFA on the big map — the
  fun gate.
- **M5** (S11): Extraction raids.
- **M6** (S12): menus, customizer, parties, queues.
- **M7** (S13–S14): upgrade trees, cosmetic store, profile — shipped game.

## Residual risks

- **Core shaders and post effects are not a stable API.** Mojang has changed
  both several times, most recently merging the shaders in 26.x. Pin them to
  DF's client version (26.3) and retest on every DF update. Fallbacks, worst last: no screen effects (the game still
  plays, aim has no zoom); a font HUD that scales with GUI scale; a
  server-driven cursor (one round trip of lag); DF dialogs and inventory
  menus.
- **The post-effect hook.** Vanilla runs the outline post effect only while a
  glowing entity is on screen; the per-player marker must always render
  (check culling and view range in the spike).
- **Glow is global.** Every client receives every mech's glow and color; only
  the post pass hides enemy outlines, which is one more reason to gate on the
  pack.
- **Client GPU.** Post passes and outlines cost GPU on weak machines: keep the
  passes few and honor the reduced/off setting.
- **CPU at map scale.** Cost is linear in display writes, probes and live
  projectiles. The mech cap per map is whatever Stage 1 measures; machine
  guns are the projectile-count risk. LOD and idle skipping are required, not
  optional.
- **Controls fight vanilla.** Shift dismounts, F swaps hands, Q drops items,
  middle click needs a target in reach. Each relies on a cancelled event or an
  item attribute; the controls spike proves them. Fallbacks: shift via
  `pressedMovementKeys` with re-mounting; ping only within normal reach.
- **Long sight lines.** On a large map, players with a low entity distance
  setting may not see far mechs or tracers; raise `setDisplayViewRange` on
  mech parts and test at the map's longest lines.
- **Players must accept the pack.** Without it, mechs and UI are missing or
  broken, so the game gates on `isUsingResourcePack`.
- **`pack-dist` grows with every release.** Each published zip stays in the
  branch history. Fine while packs are small; once art lands, prune old zips
  from the branch tip and keep the last few the plot might still reference.
- **Plot products.** Cosmetic credits depend on DF's plot product system;
  check what DF allows a product to grant before building the store.
- **Per-player hiding must stay complete.** Every menu entity has to be hidden
  from every other player, including players who join later; a miss shows one
  player's menu to another.
- **Model limits.** Java models are boxes with limited rotation; curved armor
  needs stacked boxes or extra displays.
- **Sign conventions.** `bodyYaw` and the steer values have no documented
  frame; the side vector `(-f.z, 0, f.x)` and the strafe sign still need
  in-game calibration.
- **Precision.** DF numbers keep 3 decimals: keep positions and velocities as
  vectors, scale small numbers, use 0.001 as the smallest threshold.
- **One dispatcher.** One `playerevent command` for the whole project; every
  command surface merges into it.

## Open questions (the plan assumes the default in brackets)

1. Does FFA share the big map with Extraction (one mode at a time), or get its
   own smaller arena so both can run at once? [own arena, shared mech cap]
2. Where do a destroyed mech's carried points go? [salvage at the wreck,
   anyone can collect it]
3. Can a destroyed pilot get back into an Extraction raid? [no; spectate the
   party]
4. Do AI mechs roam Extraction as a PvE threat? [yes, small point drops]
5. Keep Training ground as a third queue card? [yes, solo practice vs AI, no
   rewards]
6. Switch fire: tap shift to toggle, or hold shift for the secondary?
   [toggle]
7. What is the medium main gun? [autocannon]
8. Do pilots ever leave the mech mid-match, Titanfall-style? [no]
9. Who makes the final models and sounds? [placeholder boxes and stock sounds
   first; final art in Blockbench]
10. Replace `minecraft:default` (all text on the plot: chat, signs, DF
    messages) with the UI's TTF font, or only use it for marked UI text?
    [only UI text; chat stays readable and familiar]
