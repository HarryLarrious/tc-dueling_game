---
description: Work one MEC Jira ticket end to end and open a PR
argument-hint: MEC-<n>
---

Work on Jira ticket **$ARGUMENTS** (project MEC on
https://harrylarrious.atlassian.net) following the "Ticket workflow" section of
CLAUDE.md exactly:

1. Read the ticket and the PLAN.md section it points to; move it to In Progress.
2. Branch from the latest `origin/main` as `mec-<n>-<short-slug>`.
3. Do the work, staying inside the ticket's scope. Any unrelated issue you find
   becomes a new MEC ticket (label `found-issue`, linked to $ARGUMENTS); then
   carry on with $ARGUMENTS.
4. Make `tc-check.sh` clean, update PLAN.md/README.md if needed, and commit as
   `MEC-<n>: ...` with no Co-Authored-By or other Claude attribution line.
5. Push and open the PR against `main` with the body template from CLAUDE.md.
6. Comment the PR link on the ticket, move it to In Review, and report the PR
   link and any new tickets.

If no ticket key was given, ask which ticket to work on.
