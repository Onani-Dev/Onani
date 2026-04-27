#!/usr/bin/env bash
# Sets up .venv-ml: Python 3.11 + tensorflow-rocm for AMD GPU training.
# Run this once inside `nix develop` so the ROCm libs are in LD_LIBRARY_PATH.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${ROOT_DIR}/.venv-ml"

# AMD ROCm 7.x channel (preferred) — falls back to PyPI tensorflow-rocm if unavailable
ROCM_CHANNEL="https://repo.radeon.com/rocm/manylinux/rocm-rel-7.1/"
TF_ROCM_FALLBACK_CHANNEL="https://repo.radeon.com/rocm/manylinux/rocm-rel-6.2/"

# Locate Python 3.12 (must be provided by nix develop)
PY312="$(command -v python3.12 2>/dev/null || true)"
if [[ -z "${PY312}" ]]; then
  echo "ERROR: python3.12 not found. Run this script inside 'nix develop'." >&2
  exit 1
fi
echo "Using Python: ${PY312} ($(${PY312} --version))"

# Create venv if not present
if [[ ! -d "${VENV}" ]]; then
  echo "Creating ${VENV} ..."
  "${PY312}" -m venv "${VENV}"
fi

# Bootstrap pip in case it's not present in the venv
if ! "${VENV}/bin/python" -m pip --version >/dev/null 2>&1; then
  echo "Bootstrapping pip ..."
  "${VENV}/bin/python" -m ensurepip --upgrade
fi

PIP="${VENV}/bin/pip"
"${PIP}" install --upgrade pip --quiet

PY_VER="$("${VENV}/bin/python" -c 'import sys; print(f"cp{sys.version_info.major}{sys.version_info.minor}")')"
echo "Installing tensorflow-rocm for ${PY_VER} ..."

# AMD channels serve plain directory listings, not PyPI simple indexes.
# Install directly by wheel URL.
TF_WHEEL_71="${ROCM_CHANNEL}tensorflow_rocm-2.19.1-${PY_VER}-${PY_VER}-manylinux_2_28_x86_64.whl"
TF_WHEEL_62="${TF_ROCM_FALLBACK_CHANNEL}tensorflow_rocm-2.17.0-${PY_VER}-${PY_VER}-manylinux_2_28_x86_64.whl"

if "${PIP}" install "${TF_WHEEL_71}" 2>/dev/null; then
  echo "  tensorflow-rocm 2.19.1 installed from ROCm 7.1 channel"
elif "${PIP}" install "${TF_WHEEL_62}" 2>/dev/null; then
  echo "  tensorflow-rocm 2.17.0 installed from ROCm 6.2 channel (fallback)"
else
  echo "  WARNING: Direct wheel install failed. Trying PyPI ..."
  "${PIP}" install tensorflow-rocm || "${PIP}" install tensorflow
fi

echo "Installing deepdanbooru and remaining ML deps ..."
"${PIP}" install "deepdanbooru>=1.0.4" scikit-image

echo ""
echo "Done. ML venv ready at: ${VENV}"
echo "To test GPU visibility:"
echo "  ${VENV}/bin/python -c \"import tensorflow as tf; print(tf.config.list_physical_devices())\""
