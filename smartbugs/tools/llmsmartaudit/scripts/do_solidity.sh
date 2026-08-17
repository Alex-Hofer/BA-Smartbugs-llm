#!/bin/sh
# SmartBugs entrypoint for LLMSmartAudit (solidity mode).
# Args (from config.yaml): FILENAME TIMEOUT BIN MAIN
FILENAME="$1"
TIMEOUT="$2"
BIN="$3"
MAIN="$4"

# MAIN=1: analyse only the contract the file is named after. LLMSmartAudit has
# no contract selection -- run.py takes one source *file* and feeds its text to
# the agents -- so the restriction has to happen on the input. main_contract.py
# reduces the source to that contract and the definitions it needs. No compile
# verification here: this image has no solc and the tool never compiles, so a
# reduction can only ever cost the agents context, never break a build.
# Exit 127 means the file name matched no contract; SmartBugs reserves that
# code for exactly this case.
# MAIN=0 leaves SOURCE at the file SmartBugs passed in, byte for byte.
SOURCE="$FILENAME"
if [ "$MAIN" = "1" ]; then
    MAINDIR="${TMPDIR:-/tmp}/sb_main"
    rm -rf "$MAINDIR"
    mkdir -p "$MAINDIR"
    # Keep the original basename: it ends up in the agents' prompts.
    REDUCED="$MAINDIR/$(basename "$FILENAME")"
    python3 "$BIN/main_contract.py" "$FILENAME" "$REDUCED"
    RC=$?
    if [ $RC -ne 0 ]; then
        exit $RC
    fi
    SOURCE="$REDUCED"
fi

# --- Timeout budget (AP5, docs/BA-AP5-TIMEOUT-DESIGN.md 4.1) ----------------
# Three marks out of the one TIMEOUT SmartBugs hands us:
#   70%  brake -- exported as an absolute deadline; GPTScan stops issuing LLM
#         calls and runs out on its own, writing what it confirmed so far
#   90%  net   -- 'timeout' stops the tool if the brake did not take effect
#   rest       -- belongs to this script, to salvage and write /output.json
# TIMEOUT=0 (no --timeout) leaves every one of them unset: the run then behaves
# byte for byte as it did before AP5, which keeps the earlier runs comparable.
NET=0
if [ "${TIMEOUT:-0}" -gt 0 ]; then
    BRAKE=$(( TIMEOUT * 7 / 10 ))
    NET=$(( TIMEOUT * 9 / 10 ))
    [ "$BRAKE" -lt 1 ] && BRAKE=1
    [ "$NET" -lt 1 ] && NET=1
    SB_DEADLINE_EPOCH=$(( $(date +%s) + BRAKE ))
    export SB_DEADLINE_EPOCH
    echo "SB_TIMEOUT_BUDGET timeout=${TIMEOUT}s brake=${BRAKE}s net=${NET}s"
fi

# Where audit_report.record() drops its running snapshot after every detector
# phase (AP5). Only set when a timeout is in play: without one the tool keeps
# its original behaviour of writing exactly once, at the end.
if [ "${TIMEOUT:-0}" -gt 0 ]; then
    SB_PARTIAL_REPORT="${TMPDIR:-/tmp}/sb_partial.json"
    export SB_PARTIAL_REPORT
fi

# Backend selection: everything comes from the (host-forwarded) environment.
# DeepSeek is the default/fallback provider (requirement: test setup).
PROVIDER="${LLM_PROVIDER:-deepseek}"
MODEL="${LLM_MODEL:-}"
# run.py reads the OpenAI-compatible endpoint from BASE_URL.
if [ -n "$LLM_BASE_URL" ]; then
    export BASE_URL="$LLM_BASE_URL"
fi

# Deterministic run name so the WareHouse output directory can be located:
# WareHouse/<NAME>_<ORG>_<timestamp>/ - only the timestamp varies.
BASE=$(basename "$FILENAME" .sol)
NAME="sb_$(echo "$BASE" | tr -c 'A-Za-z0-9_\n' '_')"
ORG="smartbugs"

# The snapshot writer (chatdev/audit_report.py) reads its context from the
# environment, because record() sees nothing but a phase name and a conclusion.
SB_CONTRACT_NAME="$NAME"
export SB_CONTRACT_NAME
# Make the resolved provider explicit. The script reads LLM_PROVIDER with a
# default of "deepseek" but never exports it, so a host that left it unset
# would give the snapshot provider="unknown" while the final report says
# "deepseek" --- the same run described two ways.
export LLM_PROVIDER="$PROVIDER"

echo "LLMSA_META {\"provider\":\"$PROVIDER\",\"model\":\"${MODEL:-<provider default>}\",\"filename\":\"$(basename "$FILENAME")\"}"

cd /app || exit 1
# Remove leftovers of earlier runs with the same name (paranoia; the container
# is fresh per task, but the glob below must match exactly one run).
rm -rf WareHouse/"${NAME}_${ORG}_"* 2>/dev/null

MODEL_OPT=""
if [ -n "$MODEL" ]; then
    MODEL_OPT="--model $MODEL"
fi

if [ "$NET" -gt 0 ]; then
    timeout -s TERM "$NET" python3 run.py --config SmartContractTA --org "$ORG" \
        --name "$NAME" --provider "$PROVIDER" $MODEL_OPT --task-file "$SOURCE"
else
    python3 run.py --config SmartContractTA --org "$ORG" --name "$NAME" \
        --provider "$PROVIDER" $MODEL_OPT --task-file "$SOURCE"
fi
RC=$?

# See the note in the GPTScan entrypoint: 124/137/143 all mean "stopped on
# purpose", and only 124 lands in SmartBugs' *errors* rather than *fails*.
TIMED_OUT=0
if [ "$NET" -gt 0 ]; then
    case "$RC" in
        124|137|143) TIMED_OUT=1; RC=124 ;;
    esac
fi

# Copy the machine-readable report to the fixed location SmartBugs retrieves.
REPORT=$(ls -t WareHouse/"${NAME}_${ORG}_"*/"${NAME}_audit_report.json" 2>/dev/null | head -1)
if [ -n "$REPORT" ] && [ -f "$REPORT" ]; then
    cp "$REPORT" /output.json
elif [ "$TIMED_OUT" = "1" ] && [ -f "${SB_PARTIAL_REPORT:-/nonexistent}" ]; then
    # The tool was stopped before it could write its final report, but every
    # finished detector left a complete snapshot behind. That snapshot IS the
    # result: only the detector in flight is lost (AP5).
    cp "$SB_PARTIAL_REPORT" /output.json
    echo "LLMSmartAudit: salvaged the partial report after the timeout"
else
    # Guarantee a well-formed (empty-findings) report so SmartBugs can always
    # retrieve /output.json; force a non-zero exit so the failure is visible.
    printf '%s' "{\"tool\":\"LLMSmartAudit\",\"config\":\"SmartContractTA\",\"contract\":\"$NAME\",\"provider\":\"$PROVIDER\",\"model\":\"$MODEL\",\"categories_total\":41,\"categories_checked\":0,\"checked\":[],\"summary\":\"\",\"findings\":[],\"error\":\"no report produced\"}" > /output.json
    if [ "$RC" -eq 0 ]; then
        RC=1
    fi
fi

if [ "$TIMED_OUT" = "1" ]; then
    python3 "$BIN/mark_timeout.py" /output.json net \
        "LLMSmartAudit nach ${NET}s hart beendet; Zwischenstand geborgen" \
        || echo "LLMSmartAudit: could not stamp the timeout marker"
fi

exit $RC
