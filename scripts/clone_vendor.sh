#!/usr/bin/env bash
# Re-clone the two vendored repos at the exact commits the task file was built from.
# vendor/ is gitignored; run this on any fresh machine. Does not install anything.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p vendor
clone_pin () {  # url dir commit
  if [ ! -d "vendor/$2/.git" ]; then git clone -q "$1" "vendor/$2"; fi
  git -C "vendor/$2" fetch -q --depth 1 origin "$3" && git -C "vendor/$2" checkout -q "$3"
  echo "vendor/$2 @ $(git -C "vendor/$2" rev-parse HEAD)"
}
clone_pin https://github.com/gkroiz/agent-interp-envs         agent-interp-envs         56fd0c11e6cb973b9e1f752ba7c1f35ec3f570bb
clone_pin https://github.com/NimunB/Probing-Safety-Behaviours  Probing-Safety-Behaviours  34b3d5b7de43d4d7ec4da11deb1051995362879f
