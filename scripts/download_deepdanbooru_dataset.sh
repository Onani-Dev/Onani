#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
  cat <<'EOF'
Usage:
  scripts/download_deepdanbooru_dataset.sh --site <danbooru|realbooru|sizebooru> --url <url> [options]

Required:
  --site SITE               Dataset source label (danbooru, realbooru, or sizebooru)
  --url URL                 gallery-dl URL to scrape (repeatable)

Optional:
  --base-dir DIR            Output root (default: ./dataset/deepdanbooru/raw)
  --output-dir DIR          Exact output directory for downloaded files
  --limit N                 Max posts/files via --range 1-N (default: 0 = unlimited)
  --cookies FILE            cookies.txt passed to gallery-dl
  --download-archive FILE   gallery-dl archive DB (default: <base-dir>/<site>.sqlite3)
  --extra-arg ARG           Extra gallery-dl arg (repeatable)
  --url-file FILE           Text file with one URL per line (comments allowed via '#')
  --build-manifest          Run prepare_deepdanbooru_dataset.py after download
  --manifest-dir DIR        Manifest output dir (default: ./dataset/deepdanbooru/processed/<site>)
  --min-tags N              Min tags for manifest records (default: 1)

Example:
  scripts/download_deepdanbooru_dataset.sh \
    --site danbooru \
    --url 'https://danbooru.donmai.us/posts?tags=1girl+solo+rating%3Asafe' \
    --limit 50000 \
    --build-manifest
EOF
}

site=""
urls=()
base_dir="${ROOT_DIR}/dataset/deepdanbooru/raw"
output_dir=""
limit=0
cookies=""
archive=""
build_manifest="no"
manifest_dir=""
min_tags=1
extra_args=()
MIN_FREE_GB="${ONANI_MIN_FREE_GB:-4}"

require_free_space() {
  local target_dir="$1"
  local min_gb="$2"
  local avail_kb

  avail_kb="$(df -Pk "${target_dir}" | awk 'NR==2 {print $4}')"
  if [[ -z "${avail_kb}" ]]; then
    return 0
  fi

  if (( avail_kb < min_gb * 1024 * 1024 )); then
    echo "[error] Low disk space on filesystem hosting ${target_dir}" >&2
    echo "[error] Available: $((avail_kb / 1024 / 1024)) GB, required minimum: ${min_gb} GB" >&2
    echo "[error] Set ONANI_MIN_FREE_GB to adjust the safety threshold." >&2
    exit 1
  fi
}

resolve_archive_path() {
  local requested="$1"
  local fallback_dir="$2"
  local resolved="${requested}"

  if [[ -n "${resolved}" ]]; then
    local archive_dir
    archive_dir="$(dirname "${resolved}")"
    if [[ ! -d "${archive_dir}" ]]; then
      mkdir -p "${archive_dir}" 2>/dev/null || true
    fi

    if [[ ! -d "${archive_dir}" || ! -w "${archive_dir}" ]]; then
      echo "[warn] archive directory is not writable: ${archive_dir}" >&2
      resolved=""
    elif [[ -e "${resolved}" && ! -w "${resolved}" ]]; then
      echo "[warn] archive DB is not writable: ${resolved}" >&2
      resolved=""
    fi
  fi

  if [[ -z "${resolved}" ]]; then
    mkdir -p "${fallback_dir}"
    resolved="${fallback_dir}/${site}_archive_$(date +%Y%m%d_%H%M%S).sqlite3"
    echo "[warn] using fallback writable archive DB: ${resolved}" >&2
  fi

  printf '%s\n' "${resolved}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --site)
      site="${2:-}"
      shift 2
      ;;
    --url)
      urls+=("${2:-}")
      shift 2
      ;;
    --url-file)
      url_file="${2:-}"
      if [[ ! -f "${url_file}" ]]; then
        echo "--url-file not found: ${url_file}" >&2
        exit 1
      fi
      while IFS= read -r line || [[ -n "${line}" ]]; do
        trimmed="${line%%#*}"
        trimmed="${trimmed%$'\r'}"
        # shellcheck disable=SC2001
        trimmed="$(echo "${trimmed}" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')"
        [[ -z "${trimmed}" ]] && continue
        urls+=("${trimmed}")
      done < "${url_file}"
      shift 2
      ;;
    --base-dir)
      base_dir="${2:-}"
      shift 2
      ;;
    --output-dir)
      output_dir="${2:-}"
      shift 2
      ;;
    --limit)
      limit="${2:-0}"
      shift 2
      ;;
    --cookies)
      cookies="${2:-}"
      shift 2
      ;;
    --download-archive)
      archive="${2:-}"
      shift 2
      ;;
    --extra-arg)
      extra_args+=("${2:-}")
      shift 2
      ;;
    --build-manifest)
      build_manifest="yes"
      shift
      ;;
    --manifest-dir)
      manifest_dir="${2:-}"
      shift 2
      ;;
    --min-tags)
      min_tags="${2:-1}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${site}" || ${#urls[@]} -eq 0 ]]; then
  echo "--site and at least one --url (or --url-file) are required" >&2
  usage
  exit 1
fi

case "${site}" in
  danbooru|realbooru|sizebooru)
    ;;
  *)
    echo "Unsupported --site '${site}'. Use danbooru, realbooru, or sizebooru." >&2
    exit 1
    ;;
esac

if ! command -v gallery-dl >/dev/null 2>&1; then
  echo "gallery-dl is required but was not found in PATH" >&2
  exit 1
fi

if [[ -n "${output_dir}" ]]; then
  site_dir="${output_dir}"
else
  site_dir="${base_dir}/${site}"
fi
mkdir -p "${site_dir}"

if [[ -z "${archive}" ]]; then
  archive="${base_dir}/${site}.sqlite3"
fi

archive="$(resolve_archive_path "${archive}" "${site_dir}")"

cmd=(
  gallery-dl
  --config-ignore
  --directory "${site_dir}"
  --download-archive "${archive}"
  --option "extractor.blacklist=ytdl,ytdl-generic"
  --option "extractor.archive-format={id}"
  --post-filter "extension in ('jpg', 'jpeg', 'png')"
  --write-tags
  --write-metadata
  --no-input
)

# Sizebooru tag-search extractor always returns id=0; use file_url which is unique per post
if [[ "${site}" == "sizebooru" ]]; then
  cmd+=(--option "extractor.sizebooru.archive-format={file_url}")
  # filename field contains the unique post ID (e.g. "286797?source=search&q=giantess")
  cmd+=(--option "extractor.sizebooru.filename={filename}.{extension}")
fi

if [[ -n "${cookies}" ]]; then
  cmd+=(--cookies "${cookies}")
fi

for arg in "${extra_args[@]}"; do
  cmd+=("${arg}")
done

for url in "${urls[@]}"; do
  require_free_space "${site_dir}" "${MIN_FREE_GB}"

  run_modes=(primary)
  if [[ "${site}" == "realbooru" ]] \
    && [[ "${url}" == *"page=post"* ]] \
    && [[ "${url}" == *"s=list"* ]] \
    && [[ "${url}" == *"tags="* ]]; then
    # Realbooru page 0 can be shorter than the extractor's expected page size,
    # causing an early stop. A second pass starting at item 43 resumes crawl.
    run_modes+=(resume)
  fi

  for mode in "${run_modes[@]}"; do
    run_cmd=("${cmd[@]}")

    if [[ "${limit}" -gt 0 ]]; then
      if [[ "${mode}" == "resume" ]]; then
        if [[ "${limit}" -le 42 ]]; then
          continue
        fi
        run_cmd+=(--range "43-${limit}")
      else
        upper="${limit}"
        # Only Realbooru needs the 1-42 primary cap; it gets a separate resume
        # pass (43-limit) to work around its first-page truncation bug.
        # Danbooru and Sizebooru can take the full range in one shot.
        if [[ "${site}" == "realbooru" && "${upper}" -gt 42 ]]; then
          upper=42
        fi
        run_cmd+=(--range "1-${upper}")
      fi
    else
      if [[ "${mode}" == "resume" ]]; then
        run_cmd+=(--range "43-")
      fi
    fi

    run_cmd+=("${url}")
    echo "Running: ${run_cmd[*]}"
    "${run_cmd[@]}"
  done
done

if [[ "${build_manifest}" == "yes" ]]; then
  if [[ -z "${manifest_dir}" ]]; then
    manifest_dir="${ROOT_DIR}/dataset/deepdanbooru/processed/${site}"
  fi

  python3 "${ROOT_DIR}/scripts/prepare_deepdanbooru_dataset.py" \
    --input-dir "${site_dir}" \
    --output-dir "${manifest_dir}" \
    --min-tags "${min_tags}"
fi
