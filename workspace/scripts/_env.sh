# Sourced by the other scripts: locates the project root and loads icm-project/github.env.
ICM_WORKSPACE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ICM_ROOT="$(cd "$ICM_WORKSPACE/.." && pwd)"
ENV_FILE="$ICM_ROOT/icm-project/github.env"
[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE (run workspace/setup/install.sh)" >&2; exit 1; }
# shellcheck source=/dev/null
. "$ENV_FILE"
: "${GH_OWNER:?}" "${GH_REPO:?}" "${GH_PROJECT_NUMBER:?}"
