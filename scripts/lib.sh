# Shared helpers for the Dev and Preview scripts. Sourced, never executed:
#   . "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
# Scripts set their own shell options (set -euo pipefail). Host-specific values come from
# dev/host.env only; nothing in here carries a machine-specific path.

FH_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FH_ROOT="$(cd "$FH_LIB_DIR/.." && pwd)"

# Where the .ha-* directories (config volumes, certificates, locks, deploy work dirs) live. Always
# dev/ in real use; tests point it at a temp directory so they never touch the real state.
FH_STATE_DIR="${FH_STATE_DIR:-$FH_ROOT/dev}"
# Host-specific values file; dev/host.env unless a test points it elsewhere.
FH_HOST_ENV="${FH_HOST_ENV:-$FH_ROOT/dev/host.env}"

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
  [ -f "$FH_HOST_ENV" ] || fh_die "dev/host.env not found: copy dev/host.env.example to dev/host.env and edit it"
  set -a
  # shellcheck disable=SC1091
  . "$FH_ROOT/versions.env"
  # shellcheck disable=SC1090
  . "$FH_HOST_ENV"
  set +a
}

# fh_compose ENV ARGS...: docker compose for one environment (dev or preview).
fh_compose() {
  local env_name="${1:?fh_compose needs an environment name}"
  shift
  (
    cd "$FH_ROOT" || exit 1
    docker compose -p "familyhub-${env_name}" \
      --env-file versions.env --env-file "$FH_HOST_ENV" \
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
    --env-file "$FH_HOST_ENV" \
    -v "$FH_ROOT:/work:ro" \
    -v "$FH_ROOT/dev/.ha-secrets:/work/dev/.ha-secrets" \
    -w /work \
    --entrypoint python3 \
    "ghcr.io/home-assistant/home-assistant:${HA_VERSION}" \
    -B -m tools.seed --target "$env_name" "$@"
}

# Create the local CA and server certificate (scripts/make-certs, plan 02-01) only when absent.
fh_ensure_certs() {
  if [ -f "$FH_STATE_DIR/.ha-certs/fullchain.pem" ]; then
    return 0
  fi
  [ -x "$FH_ROOT/scripts/make-certs" ] || fh_die "scripts/make-certs is missing or not executable"
  fh_info "Creating local certificates in dev/.ha-certs"
  mkdir -p "$FH_STATE_DIR/.ha-certs"
  if [ -n "${PREVIEW_HOST_IP:-}" ]; then
    "$FH_ROOT/scripts/make-certs" --out "$FH_STATE_DIR/.ha-certs" --ip "$PREVIEW_HOST_IP"
  else
    "$FH_ROOT/scripts/make-certs" --out "$FH_STATE_DIR/.ha-certs"
  fi
}

# fh_ensure_config ENV: seed dev/.ha-ENV/configuration.yaml from the template, only when absent.
fh_ensure_config() {
  local env_name="${1:?fh_ensure_config needs an environment name}"
  local dir="$FH_STATE_DIR/.ha-${env_name}"
  local template="$FH_ROOT/dev/config-template/configuration.yaml"
  if [ -f "$dir/configuration.yaml" ]; then
    return 0
  fi
  [ -f "$template" ] || fh_die "dev/config-template/configuration.yaml is missing"
  mkdir -p "$dir"
  cp "$template" "$dir/configuration.yaml"
  fh_info "Created dev/.ha-${env_name}/configuration.yaml from the template"
}

# "Preview" or "Dev": how messages name an environment.
fh_env_label() {
  case "${1:?fh_env_label needs an environment name}" in
    preview) echo "Preview" ;;
    dev) echo "Dev" ;;
    *) echo "$1" ;;
  esac
}

# fh_lock ENV: one deploy, reset or refresh at a time per environment. The lock is an flock on file
# descriptor 9 of the calling script, so it is released when that script exits (or is killed).
# A second run exits 1 here, before it has touched anything.
fh_lock() {
  local env_name="${1:?fh_lock needs an environment name}"
  local dir="$FH_STATE_DIR/.ha-locks"
  mkdir -p "$dir"
  exec 9>"$dir/${env_name}.lock"
  if ! flock -n 9; then
    echo "ERROR: $(fh_env_label "$env_name") is busy (another deploy, reset or refresh is running)" >&2
    exit 1
  fi
}

# The separator of the build stamp: a middle dot (U+00B7) with one space either side. Spelled as
# bytes so the result does not depend on the locale this script is run in.
FH_MIDDOT=$'\302\267'

# fh_export_build REF OUT ENVWORD: export custom_components/family_hub from the git ref with git
# archive (never the working tree, so uncommitted edits cannot be deployed) into OUT, fill the three
# build tokens of the exported calendar card only, and write OUT/fh-build.env. The integration ends up
# in OUT/custom_components/family_hub. Nothing is written when REF does not resolve.
fh_export_build() {
  local ref="${1:?fh_export_build needs a git ref}"
  local out="${2:?fh_export_build needs an output directory}"
  local envword="${3:?fh_export_build needs the environment word}"
  local sha short version deployed card token count tmp

  sha=$(git -C "$FH_ROOT" rev-parse --verify --quiet "${ref}^{commit}") ||
    fh_die "git ref '$ref' does not resolve to a commit in this clone: nothing was exported"
  short="${sha:0:7}"
  case "$envword" in
    *[!A-Za-z]* | "") fh_die "environment word '$envword' must be letters only" ;;
  esac

  mkdir -p "$out"
  (
    set -o pipefail
    git -C "$FH_ROOT" archive "$sha" custom_components/family_hub | tar -x -C "$out"
  ) || fh_die "git archive of $short failed"
  local integration="$out/custom_components/family_hub"
  card="$integration/card/family-week-calendar-card.js"
  [ -f "$card" ] || fh_die "the export of $short has no card/family-week-calendar-card.js"

  version=$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$integration/manifest.json" | head -n 1)
  case "$version" in
    "" | *[!0-9A-Za-z._+-]*) fh_die "cannot read a usable version from the exported manifest.json (got '$version')" ;;
  esac
  # Host time zone comes from dev/host.env (TZ, exported by fh_load_env). %e pads the day with a space.
  deployed=$(LC_ALL=C date +'%e %b %H:%M')
  deployed="${deployed# }"

  for token in __FH_BUILD_ENV__ __FH_BUILD_VERSION__ __FH_BUILD_TIME__; do
    count=$(grep -o -- "$token" "$card" | wc -l | tr -d ' ' || true)
    [ "$count" = "1" ] || fh_die "expected the token $token exactly once in the exported card, found $count"
  done
  tmp="$card.stamp.tmp"
  sed -e "s|__FH_BUILD_ENV__|${envword}|" \
    -e "s|__FH_BUILD_VERSION__|${version}+${short}|" \
    -e "s|__FH_BUILD_TIME__|${deployed}|" "$card" >"$tmp" && mv "$tmp" "$card" ||
    fh_die "stamping the exported card failed"
  for token in __FH_BUILD_ENV__ __FH_BUILD_VERSION__ __FH_BUILD_TIME__; do
    count=$(grep -o -- "$token" "$card" | wc -l | tr -d ' ' || true)
    [ "$count" = "0" ] || fh_die "the token $token is still in the exported card after stamping"
  done

  {
    echo "FH_SHA=$sha"
    echo "FH_SHORT=$short"
    echo "FH_VERSION=$version"
    echo "FH_DEPLOYED=\"$deployed\""
    echo "FH_STAMP=\"${envword} ${FH_MIDDOT} ${version}+${short} ${FH_MIDDOT} ${deployed}\""
  } >"$out/fh-build.env"
}

# fh_swap_integration ENV SRC: put the exported integration SRC in place of the live copy. The live
# copy is moved aside to $FH_DEPLOY_WORK/previous (same file system, so both moves are renames) and
# is deleted only later, by the caller, once the new copy has been verified as served.
fh_swap_integration() {
  local env_name="${1:?fh_swap_integration needs an environment name}"
  local src="${2:?fh_swap_integration needs the exported integration directory}"
  local live="$FH_STATE_DIR/.ha-${env_name}/custom_components/family_hub"
  [ -n "${FH_DEPLOY_WORK:-}" ] || fh_die "FH_DEPLOY_WORK is not set"
  [ -f "$src/manifest.json" ] || fh_die "nothing to swap in: $src has no manifest.json"
  mkdir -p "$(dirname "$live")"
  if [ -e "$live" ]; then
    mv "$live" "$FH_DEPLOY_WORK/previous" || fh_die "could not move the live copy aside"
  fi
  mv "$src" "$live" || fh_die "could not move the new copy into place"
}
