#!/bin/sh
# SmartBugs entrypoint for GPTScan (solidity mode).
# Args (from config.yaml): FILENAME TIMEOUT BIN MAIN
FILENAME="$1"
TIMEOUT="$2"
BIN="$3"
MAIN="$4"

# Make the solc binary SmartBugs dropped into $BIN available to GPTScan/falcon.
export PATH="$BIN:$PATH"
chmod +x "$BIN/solc" 2>/dev/null || true

# MAIN=1: analyse only the contract the file is named after. GPTScan has no
# contract selection -- src/tasks.py::simple_cli takes a source *directory* and
# reports on everything that compiles in it -- so the restriction has to happen
# on the input. main_contract.py reduces the source to that contract and the
# definitions it needs, verifies with solc that the result still compiles, and
# restores the full source if it does not. Exit 127 means the file name matched
# no contract; SmartBugs reserves that code for exactly this case.
# MAIN=0 leaves SOURCE at the file SmartBugs passed in, byte for byte.
SOURCE="$FILENAME"
if [ "$MAIN" = "1" ]; then
    MAINDIR="${TMPDIR:-/tmp}/sb_main"
    rm -rf "$MAINDIR"
    mkdir -p "$MAINDIR"
    # Keep the original basename: GPTScan reports the file it analysed.
    REDUCED="$MAINDIR/$(basename "$FILENAME")"
    python3 "$BIN/main_contract.py" --verify-compile "$FILENAME" "$REDUCED"
    RC=$?
    if [ $RC -ne 0 ]; then
        exit $RC
    fi
    SOURCE="$REDUCED"
fi

# GPTScan expects a *folder* containing a single .sol file, and silently
# produces empty output if the path contains certain keywords
# (external/openzeppelin/uniswap/pancakeswap/legacy/test). /work/input is safe.
WORK=/work/input
rm -rf "$WORK"
mkdir -p "$WORK"
cp "$SOURCE" "$WORK/"

# Backend selection: provider/model come from the (host-forwarded) environment,
# defaulting to deepseek / the provider's cheap tier. The API key arrives via
# DEEPSEEK_API_KEY / OPENAI_API_KEY, forwarded by the patched sb/docker.py.
PROVIDER="${GPTSCAN_PROVIDER:-deepseek}"
MODEL_OPT=""
if [ -n "$GPTSCAN_MODEL" ]; then
    MODEL_OPT="--model $GPTSCAN_MODEL"
fi
DRY_OPT=""
if [ "${GPTSCAN_DRY_RUN:-0}" = "1" ]; then
    DRY_OPT="--dry-run"
fi

cd /opt/gptscan/src || exit 1
echo "GPTScan: provider=$PROVIDER model=${GPTSCAN_MODEL:-<default>} dry_run=${GPTSCAN_DRY_RUN:-0}"
python3 main.py -s "$WORK" -o /output.json --provider "$PROVIDER" $MODEL_OPT $DRY_OPT --format json
RC=$?

# Surface the run metadata (tokens / cost / llm_calls) on a single line so the
# SmartBugs parser can record it without a second output file.
if [ -f /output.json.metadata.json ]; then
    echo "GPTSCAN_META $(tr -d '\r\n' < /output.json.metadata.json)"
fi

# Make sure the expected output file exists even when GPTScan found nothing /
# failed early, so SmartBugs can always retrieve it.
if [ ! -f /output.json ]; then
    echo '{"version":"1.1.0","success":false,"message":"no output produced","results":[]}' > /output.json
fi

exit $RC
