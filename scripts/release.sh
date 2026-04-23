#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

usage() {
  echo "Usage: $0 [--set <version> | --bump-beta] [--no-push]"
  exit 1
}

push_changes="yes"
sync_args=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --set)
      shift
      [[ $# -gt 0 ]] || usage
      sync_args+=("--set" "$1")
      ;;
    --bump-beta)
      sync_args+=("--bump-beta")
      ;;
    --no-push)
      push_changes="no"
      ;;
    *)
      usage
      ;;
  esac
  shift
done

./scripts/sync-version.sh "${sync_args[@]}"

new_version="$(tr -d '[:space:]' < VERSION)"
tag="v${new_version}"

if git rev-parse "${tag}" >/dev/null 2>&1; then
  echo "ERROR: Tag already exists: ${tag}" >&2
  exit 1
fi

git add -A

if git diff --cached --quiet; then
  echo "No changes to commit."
else
  git commit -m "chore(release): ${tag}"
fi

git tag -a "${tag}" -m "Release ${tag}"

if [[ "${push_changes}" == "yes" ]]; then
  git push origin HEAD
  git push origin "${tag}"
fi

echo "Release prepared: ${tag}"
