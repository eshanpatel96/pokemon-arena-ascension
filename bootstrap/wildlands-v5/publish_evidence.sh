#!/usr/bin/env bash
# Publish text evidence, runtime screenshots and the patched engine C/H source
# to dedicated branches so results are reviewable without Actions artifact
# downloads. NEVER publishes .gba/.sav/.elf binaries.
set -u
trap 'echo "::warning::publish line $LINENO failed: $BASH_COMMAND"' ERR
REPO_URL="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
RUN="${GITHUB_RUN_ID}"
SHA="${GITHUB_SHA}"
WORK="${RUNNER_TEMP:-/tmp}/publish"
rm -rf "$WORK"; mkdir -p "$WORK"

push_dir() { # branch srcdir subdir message
  local branch="$1" src="$2" sub="$3" msg="$4" dir="$WORK/$branch"
  if git ls-remote --exit-code "$REPO_URL" "refs/heads/$branch" >/dev/null 2>&1 && git clone -q --depth 1 --branch "$branch" "$REPO_URL" "$dir" 2>/dev/null; then :; else
    mkdir -p "$dir"; git -C "$dir" init -q; git -C "$dir" checkout -q --orphan "$branch"
    git -C "$dir" remote add origin "$REPO_URL"
  fi
  rm -rf "$dir/$sub"; mkdir -p "$dir/$sub"; cp -r "$src"/. "$dir/$sub/"
  git -C "$dir" config user.name "wildlands-ci"; git -C "$dir" config user.email "ci@users.noreply.github.com"
  git -C "$dir" add -A
  if git -C "$dir" diff --cached --quiet; then echo "no change for $branch"; return 0; fi
  git -C "$dir" commit -q -m "$msg"
  for i in 1 2 3; do
    git -C "$dir" push -q origin "$branch" && return 0
    git -C "$dir" pull -q --rebase origin "$branch" || true
  done
  echo "::warning::push to $branch failed"
}

# 1. Evidence (text + png only)
E="$WORK/ev"; mkdir -p "$E"
if [ -d evidence ]; then
  (cd evidence && find . -type f \( -name '*.txt' -o -name '*.json' -o -name '*.log' -o -name '*.png' -o -name '*.h' \) \
     ! -name 'symbols.txt' -print0 | xargs -0 -I{} cp --parents {} "$E/")
  [ -f evidence/symbols.txt ] && gzip -c evidence/symbols.txt > "$E/symbols.txt.gz"
  [ -f evidence/build.log ] && tail -c 60000 evidence/build.log > "$E/build.log"
fi
[ -f delivery/manifest.json ] && cp delivery/manifest.json "$E/delivery-manifest.json"
echo "{\"run\":\"$RUN\",\"sha\":\"$SHA\",\"workflow\":\"${GITHUB_WORKFLOW}\",\"ref\":\"${GITHUB_REF_NAME}\"}" > "$E/run.json"
push_dir wildlands-evidence "$E" "runs/$RUN" "evidence run $RUN for $SHA"

# 2. Patched engine source snapshot (C/H/INC text only, our code + open-source upstream)
if [ -d engine/src ]; then
  S="$WORK/src"; mkdir -p "$S"
  (cd engine && find src include -type f \( -name '*.c' -o -name '*.h' -o -name '*.inc' \) -size -400k -print0 | xargs -0 -I{} cp --parents {} "$S/")
  (cd engine && ls tools/arena 2>/dev/null > "$S/tools-arena.txt"; cp Makefile "$S/Makefile.txt" 2>/dev/null; cp ld_script*.txt "$S/" 2>/dev/null) || true
  push_dir wildlands-engine-src "$S" "snapshot" "engine snapshot $SHA (run $RUN)"
fi
exit 0
