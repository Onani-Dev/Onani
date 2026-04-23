#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION_FILE="${ROOT_DIR}/VERSION"
PYPROJECT_FILE="${ROOT_DIR}/pyproject.toml"

usage() {
  echo "Usage: $0 [--set <version>] [--bump-beta|--bump-patch|--bump-minor|--bump-major]"
  exit 1
}

if [[ ! -f "${VERSION_FILE}" ]]; then
  echo "ERROR: VERSION file not found at ${VERSION_FILE}" >&2
  exit 1
fi

if [[ ! -f "${PYPROJECT_FILE}" ]]; then
  echo "ERROR: pyproject.toml not found at ${PYPROJECT_FILE}" >&2
  exit 1
fi

to_pep440() {
  local semver="$1"

  if [[ "${semver}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return
  fi

  if [[ "${semver}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-beta\.([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}b${BASH_REMATCH[2]}"
    return
  fi

  if [[ "${semver}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-alpha\.([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}a${BASH_REMATCH[2]}"
    return
  fi

  if [[ "${semver}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)-rc\.([0-9]+)$ ]]; then
    echo "${BASH_REMATCH[1]}rc${BASH_REMATCH[2]}"
    return
  fi

  echo "ERROR: Cannot convert VERSION '${semver}' to a valid PEP 440 version" >&2
  exit 1
}

new_version=""
mode=""

set_mode() {
  local next_mode="$1"
  if [[ -n "${mode}" && "${mode}" != "${next_mode}" ]]; then
    echo "ERROR: Only one bump mode can be used at a time" >&2
    usage
  fi
  mode="${next_mode}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --set)
      set_mode "set"
      shift
      [[ $# -gt 0 ]] || usage
      new_version="$1"
      ;;
    --bump-beta)
      set_mode "bump-beta"
      ;;
    --bump-patch)
      set_mode "bump-patch"
      ;;
    --bump-minor)
      set_mode "bump-minor"
      ;;
    --bump-major)
      set_mode "bump-major"
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
  elif [[ "${current_version}" =~ ^([0-9]+\.[0-9]+\.[0-9]+)$ ]]; then
    new_version="${BASH_REMATCH[1]}-beta.1"
  else
    echo "ERROR: VERSION must match x.y.z or x.y.z-beta.N for --bump-beta" >&2
    exit 1
  fi
elif [[ "${mode}" == "bump-patch" || "${mode}" == "bump-minor" || "${mode}" == "bump-major" ]]; then
  if [[ "${current_version}" =~ ^([0-9]+)\.([0-9]+)\.([0-9]+)(-[0-9A-Za-z.-]+)?$ ]]; then
    major="${BASH_REMATCH[1]}"
    minor="${BASH_REMATCH[2]}"
    patch="${BASH_REMATCH[3]}"
  else
    echo "ERROR: VERSION must match x.y.z or x.y.z-qualifier for semantic bumps" >&2
    exit 1
  fi

  case "${mode}" in
    bump-patch)
      patch="$((patch + 1))"
      ;;
    bump-minor)
      minor="$((minor + 1))"
      patch="0"
      ;;
    bump-major)
      major="$((major + 1))"
      minor="0"
      patch="0"
      ;;
  esac

  # Semantic bumps produce stable versions.
  new_version="${major}.${minor}.${patch}"
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

pep440_version="$(to_pep440 "${new_version}")"
perl -0777 -i -pe "s/(^version\s*=\s*\")[^\"]+(\"\s*$)/\${1}${pep440_version}\${2}/m" "${PYPROJECT_FILE}"

if command -v npm >/dev/null 2>&1; then
  npm --prefix "${ROOT_DIR}/frontend" version "${new_version}" --no-git-tag-version --allow-same-version >/dev/null
else
  pkg_json="${ROOT_DIR}/frontend/package.json"
  pkg_lock="${ROOT_DIR}/frontend/package-lock.json"

  perl -0777 -i -pe "s/(\"version\"\s*:\s*\")[^\"]+(\${2})/\${1}${new_version}\${2}/" "${pkg_json}"
  perl -0777 -i -pe "s/(\"version\"\s*:\s*\")[^\"]+(\${2})/\${1}${new_version}\${2}/" "${pkg_lock}"
fi

example_compose="${ROOT_DIR}/docker-compose.example.yml"
if [[ -f "${example_compose}" ]]; then
  perl -0777 -i -pe "s/(image:\s*\S+-app:)[^\s]+/\${1}${new_version}/g" "${example_compose}"
  perl -0777 -i -pe "s/(image:\s*\S+-celery:)[^\s]+/\${1}${new_version}/g" "${example_compose}"
  perl -0777 -i -pe "s/(image:\s*\S+-app-ml:)[^\s]+/\${1}${new_version}/g" "${example_compose}"
  perl -0777 -i -pe "s/(image:\s*\S+-celery-ml:)[^\s]+/\${1}${new_version}/g" "${example_compose}"
fi

echo "Synced version: ${new_version} (pyproject: ${pep440_version})"
