# task-gaming-forensics

When a language model claims success on a task it could not complete, is it lying or bullshitting?
A ~16-hour research project for Neel Nanda's MATS 12.0 application. Deception probe on Qwen3.5-9B,
tasks from Neel's team's released task-gaming environments, chain-of-thought reading, resampling interventions.

## Start here (humans and agents)

| File | What it is |
|---|---|
| `CLAUDE.md` | Standing rules for every Claude Code session: reporting protocol, gates, no installs without asking |
| `BRIEF.md` | The full plan: goal, model, task set, steps with time boxes, kill-the-result checks, deliverables |
| `STATUS.md` | Always-current state: where we are, what numbers mean, what is waiting on Nimun, next actions |
| `CHANGELOG.md` | Append-only timestamped history of every step, with numbers and abandoned approaches |
| `scripts/BOX_SETUP.md` | Install and download commands for the GPU box, run only after Nimun approves |
| `scripts/clone_vendor.sh` | Re-clones the two vendored repos at pinned commits (no installs) |
| `task_gaming/tasks.json` | The frozen task set; built by `task_gaming/build_tasks.py`, readable in `experiments/tasks_review.md` |

Vendored (gitignored, pinned): `gkroiz/agent-interp-envs` (task-gaming environments, MIT) and
`NimunB/Probing-Safety-Behaviours` (the MSc probing pipeline).
