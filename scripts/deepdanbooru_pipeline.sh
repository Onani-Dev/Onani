#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAW_DIR="${ROOT_DIR}/dataset/deepdanbooru/raw"
DATASET_DIR="${ROOT_DIR}/dataset/deepdanbooru/dataset"
DATASET_DB_NAME="dataset.sqlite"
TAGS_FILE="${ROOT_DIR}/dataset/deepdanbooru/tags.txt"
PROJECT_DIR="${ROOT_DIR}/models/deepdanbooru/project"
LIMIT=25000
MIN_TAGS=1
MODE=""
RAW_FLAT_DIR=""
ALLOW_UNLIMITED="no"

ensure_flat_directory() {
  local root="$1"
  local moved=0

  if [[ ! -d "${root}" ]]; then
    return 0
  fi

  while IFS= read -r -d '' file; do
    local base target stem ext n
    base="$(basename "${file}")"
    target="${root}/${base}"
    if [[ "${file}" == "${target}" ]]; then
      continue
    fi

    if [[ -e "${target}" ]]; then
      stem="${base%.*}"
      ext="${base##*.}"
      if [[ "${stem}" == "${ext}" ]]; then
        stem="${base}"
        ext=""
      fi
      n=1
      while :; do
        if [[ -n "${ext}" ]]; then
          target="${root}/${stem}_${n}.${ext}"
        else
          target="${root}/${stem}_${n}"
        fi
        [[ ! -e "${target}" ]] && break
        n=$((n + 1))
      done
    fi

    mv "${file}" "${target}"
    moved=$((moved + 1))
  done < <(find "${root}" -mindepth 2 -type f -print0)

  find "${root}" -mindepth 1 -type d -empty -delete
  if [[ ${moved} -gt 0 ]]; then
    echo "[scrape] flattened ${moved} file(s) into ${root}"
  fi
}

usage() {
  cat <<'EOF'
Usage:
  scripts/deepdanbooru_pipeline.sh --mode <scrape|train> [options]

Modes:
  scrape     Download/scrape datasets and build exact DeepDanbooru dataset structure
  train      Train DeepDanbooru using the prepared dataset

Options:
  --mode MODE               scrape | train
  --limit N                 Max items per source for this run (default: 25000)
  --allow-unlimited         Allow --limit 0 (downloads until source ends)
  --min-tags N              Drop samples with fewer than N tags (default: 1)
  --raw-dir DIR             Raw dataset root (default: ./dataset/deepdanbooru/raw)
  --dataset-dir DIR         DeepDanbooru dataset dir (default: ./dataset/deepdanbooru/dataset)
  --tags-file FILE          tags.txt path used for project training (default: ./dataset/deepdanbooru/tags.txt)
  --project-dir DIR         DeepDanbooru project dir for train mode (default: ./models/deepdanbooru/project)

Scrape sources:
  - Realbooru: https://realbooru.com/index.php?page=post&s=list&tags=+-gif+-webm
  - Danbooru:  https://danbooru.donmai.us/posts?tags=status%3Aactive
  - Sizebooru tags: giantess, vore, pov
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)
      MODE="${2:-}"
      shift 2
      ;;
    --limit)
      LIMIT="${2:-25000}"
      shift 2
      ;;
    --allow-unlimited)
      ALLOW_UNLIMITED="yes"
      shift
      ;;
    --min-tags)
      MIN_TAGS="${2:-1}"
      shift 2
      ;;
    --raw-dir)
      RAW_DIR="${2:-}"
      shift 2
      ;;
    --processed-dir)
      # Backward-compatible alias for --dataset-dir
      DATASET_DIR="${2:-}"
      shift 2
      ;;
    --train-data-dir)
      # Backward-compatible alias for --dataset-dir
      DATASET_DIR="${2:-}"
      shift 2
      ;;
    --dataset-dir)
      DATASET_DIR="${2:-}"
      shift 2
      ;;
    --tags-file)
      TAGS_FILE="${2:-}"
      shift 2
      ;;
    --project-dir)
      PROJECT_DIR="${2:-}"
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

if [[ -z "${MODE}" ]]; then
  echo "--mode is required" >&2
  usage
  exit 1
fi

if ! [[ "${LIMIT}" =~ ^[0-9]+$ ]]; then
  echo "--limit must be a non-negative integer" >&2
  exit 1
fi

if [[ "${MODE}" == "scrape" && "${LIMIT}" -eq 0 && "${ALLOW_UNLIMITED}" != "yes" ]]; then
  echo "Refusing unlimited scrape with --limit 0." >&2
  echo "Use a finite --limit (recommended) or add --allow-unlimited to proceed intentionally." >&2
  exit 1
fi

scrape_mode() {
  RAW_FLAT_DIR="${RAW_DIR}/all"
  mkdir -p "${RAW_DIR}" "${RAW_FLAT_DIR}" "${DATASET_DIR}" "$(dirname "${TAGS_FILE}")"

  echo "[scrape] Danbooru (status:active)"
  "${ROOT_DIR}/scripts/download_deepdanbooru_dataset.sh" \
    --site danbooru \
    --base-dir "${RAW_DIR}" \
    --output-dir "${RAW_FLAT_DIR}" \
    --url 'https://danbooru.donmai.us/posts?tags=status%3Aactive' \
    --limit "${LIMIT}"

  echo "[scrape] Realbooru (+-gif +-webm)"
  "${ROOT_DIR}/scripts/download_deepdanbooru_dataset.sh" \
    --site realbooru \
    --base-dir "${RAW_DIR}" \
    --output-dir "${RAW_FLAT_DIR}" \
    --url 'https://realbooru.com/index.php?page=post&s=list&tags=+-gif+-webm' \
    --limit "${LIMIT}"

  echo "[scrape] Sizebooru (giantess + vore + pov)"
  "${ROOT_DIR}/scripts/download_deepdanbooru_dataset.sh" \
    --site sizebooru \
    --base-dir "${RAW_DIR}" \
    --output-dir "${RAW_FLAT_DIR}" \
    --download-archive "${RAW_DIR}/sizebooru.sqlite3" \
    --limit "${LIMIT}" \
    --url 'https://sizebooru.com/Search/giantess' \
    --url 'https://sizebooru.com/Search/vore' \
    --url 'https://sizebooru.com/Search/pov'

  ensure_flat_directory "${RAW_FLAT_DIR}"

  echo "[scrape] Build exact DeepDanbooru dataset structure"
  python3 "${ROOT_DIR}/scripts/build_deepdanbooru_training_dataset.py" \
    --input-dir "${RAW_FLAT_DIR}" \
    --output-dir "${DATASET_DIR}" \
    --database-name "${DATASET_DB_NAME}" \
    --min-tags "${MIN_TAGS}" \
    --tags-output "${TAGS_FILE}" \
    --clean-output

  echo "[scrape] done"
  echo "  raw:       ${RAW_DIR}"
  echo "  dataset:   ${DATASET_DIR}"
  echo "  sqlite:    ${DATASET_DIR}/${DATASET_DB_NAME}"
  echo "  tags:      ${TAGS_FILE}"
}

generate_tags_from_database() {
  local db_path="$1"
  local out_path="$2"
  python3 - <<PY
import sqlite3
from collections import Counter
from pathlib import Path

db_path = Path(${db_path@Q})
out_path = Path(${out_path@Q})
counter = Counter()

conn = sqlite3.connect(str(db_path))
try:
    for (tag_string,) in conn.execute("SELECT tag_string FROM posts"):
        if not tag_string:
            continue
        for tag in tag_string.split():
            counter[tag] += 1
finally:
    conn.close()

out_path.parent.mkdir(parents=True, exist_ok=True)
with out_path.open("w", encoding="utf-8") as f:
    for tag, _count in sorted(counter.items(), key=lambda x: (-x[1], x[0])):
        f.write(tag + "\\n")

print(f"Regenerated tags file: {out_path} ({len(counter)} tags)")
PY
}

train_mode() {
  # Resolve deepdanbooru from the active venv (.venv) or PATH
  local -a DDB_CMD
  if command -v deepdanbooru >/dev/null 2>&1 && deepdanbooru --help >/dev/null 2>&1; then
    DDB_CMD=(deepdanbooru)
  elif python3 -c "import deepdanbooru" >/dev/null 2>&1; then
    DDB_CMD=(python3 -m deepdanbooru)
  else
    echo "deepdanbooru not found. Install it into .venv: pip install deepdanbooru" >&2
    exit 1
  fi

  # CPU-only: hide GPU, cap threads to avoid OOM
  export ROCR_VISIBLE_DEVICES=""
  export CUDA_VISIBLE_DEVICES=""
  : "${ONANI_TRAIN_THREADS:=4}"
  export TF_NUM_INTRAOP_THREADS="${ONANI_TRAIN_THREADS}"
  export TF_NUM_INTEROP_THREADS=2
  export OMP_NUM_THREADS="${ONANI_TRAIN_THREADS}"
  echo "[train] CPU-only mode, ${ONANI_TRAIN_THREADS} threads"

  mkdir -p "${PROJECT_DIR}"

  if [[ ! -f "${DATASET_DIR}/${DATASET_DB_NAME}" || ! -d "${DATASET_DIR}/images" ]]; then
    echo "Training dataset missing. Building it now from raw data..."
    RAW_FLAT_DIR="${RAW_DIR}/all"
    python3 "${ROOT_DIR}/scripts/build_deepdanbooru_training_dataset.py" \
      --input-dir "${RAW_FLAT_DIR}" \
      --output-dir "${DATASET_DIR}" \
      --database-name "${DATASET_DB_NAME}" \
      --min-tags "${MIN_TAGS}" \
      --tags-output "${TAGS_FILE}" \
      --clean-output
  fi

  if [[ ! -f "${TAGS_FILE}" ]]; then
    generate_tags_from_database "${DATASET_DIR}/${DATASET_DB_NAME}" "${TAGS_FILE}"
  fi

  if [[ ! -f "${PROJECT_DIR}/project.json" ]]; then
    echo "[train] creating DeepDanbooru project: ${PROJECT_DIR}"
    "${DDB_CMD[@]}" create-project "${PROJECT_DIR}"
  fi

  cp "${TAGS_FILE}" "${PROJECT_DIR}/tags.txt"

  python3 - <<PY
import json
from pathlib import Path
project = Path(${PROJECT_DIR@Q})
project_json = project / "project.json"
config = json.loads(project_json.read_text(encoding="utf-8"))
config["database_path"] = str((Path(${DATASET_DIR@Q}) / ${DATASET_DB_NAME@Q}).resolve())
project_json.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
print(f"Updated {project_json} database_path={config['database_path']}")
PY

  echo "[train] starting training"
  # Keep training from saturating the machine unless explicitly overridden.
  : "${ONANI_TRAIN_THREADS:=2}"
  export OMP_NUM_THREADS="${ONANI_TRAIN_THREADS}"
  export OPENBLAS_NUM_THREADS="${ONANI_TRAIN_THREADS}"
  export MKL_NUM_THREADS="${ONANI_TRAIN_THREADS}"
  export NUMEXPR_NUM_THREADS="${ONANI_TRAIN_THREADS}"
  export TF_NUM_INTRAOP_THREADS="${ONANI_TRAIN_THREADS}"
  export TF_NUM_INTEROP_THREADS="1"

  if command -v ionice >/dev/null 2>&1; then
    ionice -c3 nice -n 10 "${DDB_CMD[@]}" train-project "${PROJECT_DIR}"
  else
    nice -n 10 "${DDB_CMD[@]}" train-project "${PROJECT_DIR}"
  fi
}

case "${MODE}" in
  scrape)
    scrape_mode
    ;;
  train)
    train_mode
    ;;
  *)
    echo "Invalid mode '${MODE}'. Use scrape or train." >&2
    exit 1
    ;;
esac
