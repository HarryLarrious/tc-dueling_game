# tc-dueling_game — instructions for Claude

Every Claude session working in this repo follows these rules, so the work
stays consistent no matter which session does it.

## The project

A legged-mech PvP game for DiamondFire, written in Terracotta. Read these
before changing anything:

- [PLAN.md](PLAN.md): the design, locked decisions, measured budgets, stages,
  risks and open questions. It is the source of truth; update it when a design
  fact changes.
- [README.md](README.md): the file layout.
- `references/`: art, UI mockups, controls and augment lists from the owner.

Target client: Minecraft 26.3, resource pack format 97.1. Measured caps: 20
mechs per map, 60 live projectiles (PLAN.md, CPU rules).

## Tools

- **Terracotta**: load the `terracotta` skill before writing `.tc` code. Every
  change must compile clean with
  `~/.claude/skills/terracotta/scripts/tc-check.sh .` (terracotta
  1.0.0-beta.10) before you commit. Look up names with `tc-names.py`; never
  guess them.
- **Known Terracotta gaps**: `start` and `to` are keywords, not variable names;
  DF's "Raycast to Block" is not exposed, so use `game.raycast` and get the hit
  face from the hit point.
- **The plot** (Plot 206003) is shared live state. Only place code on it
  (`tc-send.py`, `tc-clear.py`) when the user asks. In the PR, say what still
  needs testing in game.
- **Self-test**: entering play mode runs `test/selftest.tc` and prints
  `MECHTEST` lines to chat, which reach the client log. After `tc-send.py`,
  run `tools/read_selftest.sh 30 "$HOME/.claude/skills/terracotta/scripts/tc-mode.py play"`
  to switch to play and read the result (exit 0 = all passed). Add checks for
  each new feature to `runSelfTest`. Turn it off with `selfTestOnJoin()`.
  For visual checks set `selfTestDemo()` to "hud" or "fx" and take
  screenshots of the stages (`MECHTEST FX <name>` lines); set it back to "".
- **Resource pack**: every change under `pack/` must pass
  `python3 tools/build_pack.py --check` (JSON, resource-location names, and
  every shader compiled with `glslc` under the 26.3 define sets). Publish with
  `--publish`, then push `pack-dist` (on the host, see below). An overridden
  `minecraft:core/*` shader needs an entry in `tools/shader_variants.json`.
- **Minecraft source**: the `minecraft-source` MCP has the decompiled 26.3
  client, its shaders and resources. Check render and shader facts there
  instead of relying on memory.
- **VS Code flatpak**: the shell runs inside a flatpak sandbox. Run `gh` and
  `git push` on the host: `flatpak-spawn --host gh ...` and
  `flatpak-spawn --host git -C "$PWD" push ...` (git's credential helper is the
  host's `gh`).

## Code conventions

- Match the surrounding code: `/** */` doc comment on every function and
  declared global, short `//` comments only where the math is not obvious.
- Global state is declared with `declare global` (core lists in
  `core/state.tc`; a subsystem may declare its own globals at the top of its
  file).
- One `playerevent command` dispatcher for the whole project
  (`core/commands.tc`); add command branches there, never a second one.
- DF numbers keep 3 decimals: keep positions and velocities as vectors, use
  0.001 as the smallest threshold.

## Ticket workflow (Jira project MEC)

All work is tracked in Jira project **MEC** ("mechGame") on
https://harrylarrious.atlassian.net. Each PLAN.md stage is an epic; tasks sit
under their stage epic with a milestone label (M1–M7) and area labels.
Workflow transitions: To Do `11`, In Progress `21`, In Review `31`, Done `41`.

1. **Start**: read the ticket and the PLAN.md section it points to. Move it to
   In Progress.
2. **Branch** from the latest `origin/main`, one branch per ticket:
   `git fetch origin && git switch -c mec-<n>-<short-slug> origin/main`. If
   other Claude sessions may be working at the same time, use a separate git
   worktree per ticket.
3. **Work only on the ticket's scope.**
4. **Found an issue that is not this ticket's job?** Create a new MEC Task for
   it under the right stage epic, labeled `found-issue` plus an area label.
   Describe what is wrong, where (file and line), how you found it, and
   "Found while working on MEC-<n>". Link it to the current ticket
   ("Relates"), list it in the PR, then **continue the current ticket**. Do
   not fix it on this branch unless it blocks the ticket; if it does, say so
   in the PR.
5. **Finish**: `tc-check.sh` clean; PLAN.md and README.md updated if design or
   layout changed. Commit messages start with the ticket key:
   `MEC-<n>: <imperative summary>`.
   **Never add `Co-Authored-By` or any other Claude attribution line to a
   commit message.**
6. **Always open a PR when the ticket is done**: push the branch and open a PR
   against `main` with `flatpak-spawn --host gh pr create`. Title:
   `MEC-<n>: <ticket summary>`. Body:

   ```markdown
   ## Ticket
   [MEC-<n>](https://harrylarrious.atlassian.net/browse/MEC-<n>): <ticket title>

   <One or two sentences: what the ticket was about.>

   ## What changed
   - <change>

   ## Testing
   - tc-check: <clean / errors> (terracotta <version>, <N> templates)
   - In game: <what was tested, or what still needs testing on the plot>

   ## New tickets
   - <MEC-x: title, or "None">
   ```

7. **Hand off**: comment the PR link on the ticket and move it to In Review.
   Another AI reviews the PRs, checks they work together, merges them and
   moves tickets to Done. Never merge PRs, push to `main`, rewrite other
   branches, or set tickets to Done yourself.

Use `/ticket MEC-<n>` to run this workflow for one ticket.
