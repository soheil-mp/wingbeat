#!/usr/bin/env bash
# Installs the pinned toolchain inside the dev container, then sets up the workspace.
# Versions match CI (.github/workflows/ci.yml); Renovate keeps both in step.
set -euo pipefail

UV_VERSION="0.13.6"
JUST_VERSION="1.59.0"
BUF_VERSION="1.75.0"
declare -A BUF_SHA256=(
  [x86_64]="fad1e38d6909bbb583a4da81d8c02a01046e2cd663bde7e337dd24277393764b"
  [aarch64]="00eb190aa82df17f393e05b04889cc60a0b13b3259d336e21a87d5f23ab4fd26"
)

bin_dir="${HOME}/.local/bin"
mkdir -p "${bin_dir}"
export PATH="${bin_dir}:${PATH}"

echo "==> uv ${UV_VERSION}"
curl -LsSf "https://astral.sh/uv/${UV_VERSION}/install.sh" | env UV_NO_MODIFY_PATH=1 sh

echo "==> just ${JUST_VERSION}"
uv tool install --quiet "rust-just==${JUST_VERSION}"

arch="$(uname -m)"
echo "==> buf ${BUF_VERSION} (${arch})"
tmp="$(mktemp)"
curl -sSfL -o "${tmp}" "https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-Linux-${arch}"
echo "${BUF_SHA256[${arch}]}  ${tmp}" | sha256sum --check --strict --quiet
install -m 0755 "${tmp}" "${bin_dir}/buf"
rm -f "${tmp}"

echo "==> workspace"
just setup

echo "Dev container ready: run 'just' to list the recipes."
