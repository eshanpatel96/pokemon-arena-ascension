#!/usr/bin/env bash
# Publish text evidence, runtime screenshots and the patched engine C/H source
# to dedicated branches so results are reviewable without Actions artifact
# downloads. NEVER publishes .gba/.sav/.elf binaries.
echo "::notice::publish start token=${GH_TOKEN:+set} repo=${GITHUB_REPOSITORY:-unset} run=${GITHUB_RUN_ID:-unset}"
set -E
trap 'echo "::warning::publish line $LINENO failed: $BASH_COMMAND"' ERR
REPO_URL="https://x-access-token:${GH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git"
RUN="${GITHUB_RUN_ID}"
SHA="${GITHUB_SHA}"
WORK="${RUNNER_TEMP:-/tmp}/publish"
rm -rf "$WORK"; mkdir -p "$WORK"

push_dir() { # branch srcdir subdir message
  local branch="$1" src="$2" sub="$3" msg="$4" dir="$WORK/$branch"
  local G="git -c http.extraheader= -c http.https://github.com/.extraheader= -C $dir"
  rm -rf "$dir"; mkdir -p "$dir"
  $G init -q; $G remote add origin "$REPO_URL"
  if out=$($G fetch -q --depth 1 origin "$branch" 2>&1); then
    $G checkout -q -B "$branch" FETCH_HEAD
  else
    echo "::notice::fetch $branch: $(echo "$out" | head -2 | tr '\n' ' ' | sed 's/x-access-token:[^@]*@/***@/g')"
    $G checkout -q --orphan "$branch"
  fi
  rm -rf "$dir/$sub"; mkdir -p "$dir/$sub"; cp -r "$src"/. "$dir/$sub/"
  $G config user.name "wildlands-ci"; $G config user.email "ci@users.noreply.github.com"
  $G add -A
  if $G diff --cached --quiet; then echo "no change for $branch"; return 0; fi
  $G commit -q -m "$msg"
  for i in 1 2 3; do
    if out=$($G push -q origin "$branch" 2>&1); then return 0; fi
    echo "::notice::push $branch attempt $i: $(echo "$out" | head -2 | tr '\n' ' ' | sed 's/x-access-token:[^@]*@/***@/g')"
    $G fetch -q --depth 1 origin "$branch" && $G rebase -q FETCH_HEAD || true
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
push_dir wildlands-evidence "$E" "runs/$RUN" "evidence run $RUN for $SHA"; echo "::notice::evidence push rc=$?"

# 2. Patched engine source snapshot (C/H/INC text only, our code + open-source upstream)
if [ -d engine/src ]; then
  S="$WORK/src"; mkdir -p "$S"
  (cd engine && find src include -type f \( -name '*.c' -o -name '*.h' -o -name '*.inc' \) -size -400k -print0 | xargs -0 -I{} cp --parents {} "$S/")
  (cd engine && ls tools/arena 2>/dev/null > "$S/tools-arena.txt"; cp Makefile "$S/Makefile.txt" 2>/dev/null; cp ld_script*.txt "$S/" 2>/dev/null) || true
  push_dir wildlands-engine-src "$S" "snapshot" "engine snapshot $SHA (run $RUN)"
fi
exit 0
