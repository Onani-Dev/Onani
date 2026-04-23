#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/VERSION"

usage() {
  echo "Usage: $0 [--set <version>] [--bump-beta]"
  exit 1
}

if [[ ! -f "${VERSION_FILE}" ]]; then
  echo "ERROR: VERSION file not found at ${VERSION_FILE}" >&2
  exit 1
fi

new_version=""
mode=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --set)
      mode="set"
      shift
      [[ $# -gt 0 ]] || usage
      new_version="$1"
      ;;
    --bump-beta)
      mode="bump-beta"
      ;;
    *)
      usage
      ;;
  esac
  shift
done

current_version="$(tr -d '[:space:]' < "${VERSION_FILE}")"

if [[ "${mode}" == "bump-beta" ]]; then
  if [[ "${current_version}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-beta\.([0-9]+)$ ]]; then
    base="${BASH_REMATCH[1]}"
    n="${BASH_REMATCH[2]}"
    new_version="${base}-beta.$((n + 1))"
  else
    echo "ERROR: VERSION must match x.y.z-beta.N for --bump-beta" >&2
    exit 1
  fi
elif [[ "${mode}" == "set" ]]; then
  :
else
  new_version="${current_version}"
fi

if [[ ! "${new_version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$ ]]; then
  echo "ERROR: Invalid semver-like version: ${new_version}" >&2
  exit 1
fi

printf '%s\n' "${new_version}" > "${VERSION_FILE}"

if command -v npm >/dev/null 2>&1; then
  npm --prefix "${ROOT_DIR}/frontend" version "${new_version}" --no-git-tag-version --allow-same-version >/dev/null
else
  pkg_json="${ROOT_DIR}/frontend/package.json"
  pkg_lock="${ROOT_DIR}/frontend/package-lock.json"

  perl -0777 -i -pe "s/(\"name\"\s*:\s*\"frontend\"\s*,\s*\n\s*\"version\"\s*:\s*\")[^\"]+(\")/\${1}${new_version}\${2}/" "${pkg_json}"
  perl -0777 -i -pe "s/(\"name\"\s*:\s*\"frontend\"\s*,\s*\n\s*\"version\"\s*:\s*\")[^\"]+(\")/\${1}${new_version}\${2}/" "${pkg_lock}"
  perl -0777 -i -pe "s/(\"\"\s*:\s*\{\s*\n\s*\"name\"\s*:\s*\"frontend\"\s*,\s*\n\s*\"version\"\s*:\s*\")[^\"]+(\")/\${1}${new_version}\${2}/" "${pkg_lock}"
fi

echo "Synced version: ${new_version}"
