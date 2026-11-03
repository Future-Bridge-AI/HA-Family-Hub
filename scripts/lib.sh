# Shared helpers for the Dev and Preview scripts. Sourced, never executed:
#   . "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# Scripts set their own shell options (set -euo pipefail). Host-specific values come from
# dev/host.env only; nothing in here carries a machine-specific path.

FH_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FH_ROOT="$(cd "$FH_LIB_DIR/.." && pwd)"

fh_die() {
  echo "ERROR: $*" >&2
  exit 1
}

fh_info() {
  echo "==> $*"
}

# Load versions.env, then dev/host.env, exporting every key to the child processes below.
fh_load_env() {
  [ -f "$FH_ROOT/versions.env" ] || fh_die "versions.env is missing from the repository root"
  [ -f "$FH_ROOT/dev/host.env" ] || fh_die "dev/host.env not found: copy dev/host.env.example to dev/host.env and edit it"
  set -a
  # shellcheck disable=SC1091
  . "$FH_ROOT/versions.env"
  # shellcheck disable=SC1091
  . "$FH_ROOT/dev/host.env"
  set +a
}

# fh_compose ENV ARGS...: docker compose for one environment (dev or preview).
fh_compose() {
  local env_name="${1:?fh_compose needs an environment name}"
  shift
  (
    cd "$FH_ROOT" || exit 1
    docker compose -p "familyhub-${env_name}" \
      --env-file versions.env --env-file dev/host.env \
      -f dev/compose.yaml -f "dev/compose.${env_name}.yaml" "$@"
  )
}

# fh_seed ENV ARGS...: run the seed tool (tools/seed, plan 02-01) against one environment.
# Tests set FH_SEED_CMD to a stub; otherwise the tool runs in a throwaway container of the pinned HA
# image, so the host needs no Python packages. The repository is mounted read-only; only the secrets
# directory is writable, and the container runs as the calling user.
fh_seed() {
  local env_name="${1:?fh_seed needs an environment name}"
  shift
  if [ -n "${FH_SEED_CMD:-}" ]; then
    # FH_SEED_CMD is a command line, so word splitting is intended.
    # shellcheck disable=SC2086
    $FH_SEED_CMD --target "$env_name" "$@"
    return
  fi
  : "${HA_VERSION:?set in versions.env (call fh_load_env first)}"
  mkdir -p "$FH_ROOT/dev/.ha-secrets"
  chmod 700 "$FH_ROOT/dev/.ha-secrets"
  docker run --rm --network host \
    --user "$(id -u):$(id -g)" \
    -e HOME=/tmp -e PYTHONDONTWRITEBYTECODE=1 \
    --env-file "$FH_ROOT/dev/host.env" \
    -v "$FH_ROOT:/work:ro" \
    -v "$FH_ROOT/dev/.ha-secrets:/work/dev/.ha-secrets" \
    -w /work \
    --entrypoint python3 \
    "ghcr.io/home-assistant/home-assistant:${HA_VERSION}" \
    -B -m tools.seed --target "$env_name" "$@"
}

# Create the local CA and server certificate (scripts/make-certs, plan 02-01) only when absent.
fh_ensure_certs() {
  if [ -f "$FH_ROOT/dev/.ha-certs/fullchain.pem" ]; then
    return 0
  fi
  [ -x "$FH_ROOT/scripts/make-certs" ] || fh_die "scripts/make-certs is missing or not executable"
  fh_info "Creating local certificates in dev/.ha-certs"
  mkdir -p "$FH_ROOT/dev/.ha-certs"
  if [ -n "${PREVIEW_HOST_IP:-}" ]; then
    "$FH_ROOT/scripts/make-certs" --out "$FH_ROOT/dev/.ha-certs" --ip "$PREVIEW_HOST_IP"
  else
    "$FH_ROOT/scripts/make-certs" --out "$FH_ROOT/dev/.ha-certs"
  fi
}

# fh_ensure_config ENV: seed dev/.ha-ENV/configuration.yaml from the template, only when absent.
fh_ensure_config() {
  local env_name="${1:?fh_ensure_config needs an environment name}"
  local dir="$FH_ROOT/dev/.ha-${env_name}"
  local template="$FH_ROOT/dev/config-template/configuration.yaml"
  if [ -f "$dir/configuration.yaml" ]; then
    return 0
  fi
  [ -f "$template" ] || fh_die "dev/config-template/configuration.yaml is missing"
  mkdir -p "$dir"
  cp "$template" "$dir/configuration.yaml"
  fh_info "Created dev/.ha-${env_name}/configuration.yaml from the template"
}
