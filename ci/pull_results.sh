#!/usr/bin/env bash
# Download a workflow run's artifacts into a staging dir (never into the QG working tree) + sha256 manifest.
# Usage: ci/pull_results.sh <run-id> [repo=Macrolol/qg-l9-runs] [which=merged|results|all]
#   merged  : l9-<tag>-merged only (default; finished runs + summary.csv)
#   results : result-* per-job artifacts
#   all     : every artifact incl. prep-* and partial-* (checkpoints)
# Output: $L9_STAGING (default /workspace/projects/quantum-gravity/shared/l9-staging, falling back to legacy /workspace/qg-l9-staging)/<run-id>/{artifacts...,MANIFEST.sha256,run.json}
set -euo pipefail
id=${1:?run id}; repo=${2:-Macrolol/qg-l9-runs}; which=${3:-merged}
new=/workspace/projects/quantum-gravity/shared/l9-staging; old=/workspace/qg-l9-staging
if [ -z "${L9_STAGING:-}" ]; then if [ -d "$new" ] || [ ! -e "$old" ]; then L9_STAGING=$new; else L9_STAGING=$old; fi; fi
base=$L9_STAGING; dest="$base/$id"
case "$(realpath -m "$dest")" in /workspace/qg-unification/*) echo "refusing to write into the QG working tree" >&2; exit 2;; esac
[ -e "$dest" ] && { echo "$dest exists; not overwriting" >&2; exit 3; }
mkdir -p "$dest"
gh run view "$id" -R "$repo" --json databaseId,displayTitle,headSha,status,conclusion,createdAt,updatedAt,url,jobs > "$dest/run.json"
case "$which" in
  merged)  gh run download "$id" -R "$repo" -p 'l9-*-merged' -D "$dest" ;;
  results) gh run download "$id" -R "$repo" -p 'result-*' -D "$dest" ;;
  all)     gh run download "$id" -R "$repo" -D "$dest" ;;
  *) echo "which = merged|results|all" >&2; exit 1 ;;
esac
(cd "$dest" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256)
chmod -R a-w "$dest"
echo "staged $(wc -l < "$dest/MANIFEST.sha256") files in $dest (read-only); verify with: (cd $dest && sha256sum -c MANIFEST.sha256)"
