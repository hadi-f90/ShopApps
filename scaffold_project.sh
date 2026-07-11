#!/usr/bin/env bash
# Scaffold a multi-platform Python app project (PySide6 + Peewee + Numba/Cython for hotspots)
#
# Usage:
#   ./scaffold_project.sh <package_name> [target_dir]
#
# Example:
#   ./scaffold_project.sh myapp .
#
set -euo pipefail

PACKAGE_NAME="${1:?Usage: $0 <package_name> [target_dir]}"
TARGET_DIR="${2:-.}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

cd "${TARGET_DIR}"

echo "==> Scaffolding project for package: ${PACKAGE_NAME}"
echo "==> Target directory: $(pwd)"

# ---------------------------------------------------------------------------
# Directory tree
# ---------------------------------------------------------------------------
dirs=(
  "src/${PACKAGE_NAME}/config"
  "src/${PACKAGE_NAME}/db/migrations"
  "src/${PACKAGE_NAME}/core"
  "src/${PACKAGE_NAME}/features"
  "src/${PACKAGE_NAME}/ui/desktop/windows"
  "src/${PACKAGE_NAME}/ui/desktop/widgets"
  "src/${PACKAGE_NAME}/ui/desktop/qrc"
  "src/${PACKAGE_NAME}/locale/en"
  "src/${PACKAGE_NAME}/locale/fa"
  "native/cython_ext"
  "tests/unit"
  "tests/native"
  "assets/icons"
  "assets/fonts"
  "assets/images"
  "packaging/desktop"
  "packaging/mobile"
  "docs"
  "scripts"
  ".github/workflows"
)

for d in "${dirs[@]}"; do
  mkdir -p "$d"
  echo "  created: $d"
done

# ---------------------------------------------------------------------------
# Python package __init__.py placeholders
# ---------------------------------------------------------------------------
init_dirs=(
  "src/${PACKAGE_NAME}"
  "src/${PACKAGE_NAME}/config"
  "src/${PACKAGE_NAME}/db"
  "src/${PACKAGE_NAME}/core"
  "src/${PACKAGE_NAME}/features"
  "src/${PACKAGE_NAME}/ui"
  "src/${PACKAGE_NAME}/ui/desktop"
  "src/${PACKAGE_NAME}/ui/desktop/windows"
  "src/${PACKAGE_NAME}/ui/desktop/widgets"
)
for d in "${init_dirs[@]}"; do
  touch "$d/__init__.py"
done

touch "tests/__init__.py" "tests/unit/__init__.py"

# ---------------------------------------------------------------------------
# Root-level files
# ---------------------------------------------------------------------------
touch README.md LICENSE

cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*.egg-info/
build/
dist/

# venv
.venv/

# Qt / i18n compiled translations
*.qm

# Cython build artifacts
native/**/build/
native/**/*.c
*.so
*.pyd
*.dll

# OS
.DS_Store
EOF

cat > pyproject.toml << EOF
[project]
name = "${PACKAGE_NAME}"
version = "0.1.0"
description = ""
requires-python = ">=3.11"
dependencies = [
    "PySide6",
    "peewee",
]

[project.optional-dependencies]
# Only needed once you actually have a profiled bottleneck to address.
native = [
    "numba",
    "cython",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/${PACKAGE_NAME}"]
EOF

# ---------------------------------------------------------------------------
# Cython native extension skeleton (only used once profiling justifies it)
# ---------------------------------------------------------------------------
cat > native/cython_ext/example.pyx << 'EOF'
# Sanity-check module to confirm the Cython build pipeline works.
# Only add real code here after profiling has identified a specific,
# narrow bottleneck that Numba could not handle.

def ping() -> str:
    return "pong from cython"
EOF

cat > native/cython_ext/setup.py << EOF
from setuptools import setup
from Cython.Build import cythonize

setup(
    name="${PACKAGE_NAME}_native",
    ext_modules=cythonize("example.pyx", language_level=3),
)
EOF

echo "==> Note: native/cython_ext requires the 'native' extras (pip install -e .[native])."
echo "    Build with: cd native/cython_ext && python setup.py build_ext --inplace"
echo "==> For numeric bottlenecks, try numba's @njit decorator directly in Python first —"
echo "    no build step, no new syntax. Only reach for native/cython_ext if that's insufficient."

# ---------------------------------------------------------------------------
# Virtual environment
# ---------------------------------------------------------------------------
echo "==> Creating virtual environment at .venv"
"${PYTHON_BIN}" -m venv .venv

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install PySide6 peewee numba cython

deactivate

echo ""
echo "==> Done."
echo "    Activate the venv with:"
echo "      source .venv/bin/activate      (Linux/macOS)"
echo "      .venv\\Scripts\\activate         (Windows)"