#!/bin/sh
# SmartBugs entrypoint for LLMSmartAudit (solidity mode).
# Args (from config.yaml): FILENAME TIMEOUT BIN MAIN
FILENAME="$1"
TIMEOUT="$2"
BIN="$3"
MAIN="$4"

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

echo "LLMSA_META {\"provider\":\"$PROVIDER\",\"model\":\"${MODEL:-<provider default>}\",\"filename\":\"$(basename "$FILENAME")\"}"

cd /app || exit 1
# Remove leftovers of earlier runs with the same name (paranoia; the container
# is fresh per task, but the glob below must match exactly one run).
rm -rf WareHouse/"${NAME}_${ORG}_"* 2>/dev/null

MODEL_OPT=""
if [ -n "$MODEL" ]; then
    MODEL_OPT="--model $MODEL"
fi

python3 run.py --config SmartContractTA --org "$ORG" --name "$NAME" \
    --provider "$PROVIDER" $MODEL_OPT --task-file "$FILENAME"
RC=$?

# Copy the machine-readable report to the fixed location SmartBugs retrieves.
REPORT=$(ls -t WareHouse/"${NAME}_${ORG}_"*/"${NAME}_audit_report.json" 2>/dev/null | head -1)
if [ -n "$REPORT" ] && [ -f "$REPORT" ]; then
    cp "$REPORT" /output.json
else
    # Guarantee a well-formed (empty-findings) report so SmartBugs can always
    # retrieve /output.json; force a non-zero exit so the failure is visible.
    printf '%s' "{\"tool\":\"LLMSmartAudit\",\"config\":\"SmartContractTA\",\"contract\":\"$NAME\",\"provider\":\"$PROVIDER\",\"model\":\"$MODEL\",\"categories_total\":41,\"categories_checked\":0,\"checked\":[],\"summary\":\"\",\"findings\":[],\"error\":\"no report produced\"}" > /output.json
    if [ "$RC" -eq 0 ]; then
        RC=1
    fi
fi

exit $RC
