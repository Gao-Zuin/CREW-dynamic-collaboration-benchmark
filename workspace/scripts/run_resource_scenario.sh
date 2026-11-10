#!/usr/bin/env bash
# Run one concrete event sequence through the ORCH task runner.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCENARIO_FAMILY="${SCENARIO_FAMILY:-scenarios}"
case "$SCENARIO_FAMILY" in scenarios|fire_near_civilians|commitment_event) ;; *) echo "SCENARIO_FAMILY must be scenarios, fire_near_civilians, or commitment_event" >&2; exit 2;; esac
LEVEL="${SCENARIO:?set SCENARIO to a name from the selected tasks.json}"
ARM="${ARM:?set ARM=fixed or adaptive}"
case "$ARM" in
  fixed) export CREW_HT_FIXED_GROUPS=1 ;;
  adaptive) export CREW_HT_FIXED_GROUPS=0 ;;
  *) echo "ARM must be fixed or adaptive" >&2; exit 2 ;;
esac
MODE="$(python - "$ROOT/ORCH/crew-algorithms/crew_algorithms/wildfire_alg/config/resource_scheduling/$SCENARIO_FAMILY/tasks.json" "$LEVEL" <<'PY'
import json
import sys
rows = json.load(open(sys.argv[1]))
matches = [row for row in rows if row['id'] == sys.argv[2]]
if len(matches) != 1:
    raise SystemExit(f'Unknown scenario: {sys.argv[2]}')
print(matches[0]['design']['information_mode'])
PY
)"
case "$MODE" in
  worker_report) export CREW_HT_WORKER_EVENT_REPORT=1; export CREW_HT_LOCAL_EVENT_INFO=0 ;;
  organizer_direct|none) export CREW_HT_WORKER_EVENT_REPORT=0; export CREW_HT_LOCAL_EVENT_INFO=0 ;;
  *) echo "Unsupported information mode: $MODE" >&2; exit 2 ;;
esac
export CREW_RESOURCE_SCHEDULING_FAMILY="$SCENARIO_FAMILY"
export CREW_HT_STRUCTURAL_INITIAL_PLAN=1
export CREW_HT_ROUND_DELIVERY="${CREW_HT_ROUND_DELIVERY:-1}"
export LEVEL
export SEED="${SEED:-42}"
export MAX_STEPS="${MAX_STEPS:-100}"
export RUN_LOG_ROOT="${RUN_LOG_ROOT:-$ROOT/benchmark_runs/${SCENARIO_FAMILY}/${LEVEL}_seed${SEED}_${ARM}}"
exec bash "$ROOT/scripts/run_task_hypergraph.sh"
