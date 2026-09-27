#!/usr/bin/env bash
# Install a GitHub Actions runner on the k3s control plane for this repository.
# Does not touch a runner installed for another project.
set -euo pipefail

: "${RUNNER_TOKEN:?RUNNER_TOKEN is required}"

REPO_URL="${REPO_URL:-https://github.com/blezzed/zingsa_collect}"
RUNNER_NAME="${RUNNER_NAME:-$(hostname)}"
RUNNER_LABELS="${RUNNER_LABELS:-self-hosted,linux,zingsa-collect-k3s}"
INSTALL_DIR="${INSTALL_DIR:-}"

arch="$(uname -m)"
case "$arch" in
  x86_64) runner_arch="x64" ;;
  aarch64|arm64) runner_arch="arm64" ;;
  *)
    echo "Unsupported architecture: ${arch}" >&2
    exit 1
    ;;
esac

if [ -z "$INSTALL_DIR" ]; then
  if sudo -n true >/dev/null 2>&1; then
    INSTALL_DIR="/opt/actions-runner-zingsa-collect"
  else
    INSTALL_DIR="${HOME}/actions-runner-zingsa-collect"
  fi
fi

if [ -z "${RUNNER_VERSION:-}" ]; then
  RUNNER_VERSION="$(
    curl -fsSL https://api.github.com/repos/actions/runner/releases/latest \
      | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"].lstrip("v"))'
  )"
fi

if sudo -n true >/dev/null 2>&1; then
  sudo mkdir -p "$INSTALL_DIR"
  sudo chown "$(id -u):$(id -g)" "$INSTALL_DIR"
else
  mkdir -p "$INSTALL_DIR"
fi

tarball="${INSTALL_DIR}/actions-runner.tar.gz"
curl -fsSL -o "$tarball" \
  "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${runner_arch}-${RUNNER_VERSION}.tar.gz"
tar -xzf "$tarball" -C "$INSTALL_DIR"
rm -f "$tarball"

cd "$INSTALL_DIR"
./config.sh --unattended \
  --url "$REPO_URL" \
  --token "$RUNNER_TOKEN" \
  --name "$RUNNER_NAME" \
  --labels "$RUNNER_LABELS" \
  --replace

if sudo -n true >/dev/null 2>&1; then
  sudo ./svc.sh install
  sudo ./svc.sh start
  echo "Runner service started from ${INSTALL_DIR} as ${RUNNER_NAME} (${RUNNER_LABELS})."
else
  log_file="${HOME}/zingsa-collect-runner.log"
  nohup ./run.sh >>"$log_file" 2>&1 &
  marker="zingsa-collect-actions-runner"
  crontab_line="@reboot cd ${INSTALL_DIR} && ./run.sh >>${log_file} 2>&1 # ${marker}"
  (
    crontab -l 2>/dev/null | grep -v "${marker}" || true
    echo "$crontab_line"
  ) | crontab -
  echo "Passwordless sudo is not available. Runner started in the background and registered for @reboot."
fi
