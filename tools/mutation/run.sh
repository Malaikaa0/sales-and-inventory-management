#!/usr/bin/env bash
# Run a full mutation session on throwaway copies of the repository.
#   bash tools/mutation/run.sh <label> <work directory>
# Raw results go to reports/mutation/<label>.*
set -u
label=$1
work=$2
repo=$(pwd)
out="$repo/reports/mutation"
if [ -x "$repo/.venv/Scripts/python.exe" ]; then
    export PATH="$repo/.venv/Scripts:$PATH"
    interpreter="$(pwd -W)/.venv/Scripts/python.exe"
else
    interpreter=$(command -v python)
fi
export DEBUG=True PYTHONDONTWRITEBYTECODE=1
mkdir -p "$out" "$work"

pids=()
stop_workers() { for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null; done; }
trap stop_workers EXIT

# One copy per worker, plus one for the session itself.
for n in 0 1 2 3 4; do
    copy="$work/$label-$n"
    rm -rf "$copy"
    mkdir -p "$copy"
    git ls-files -co --exclude-standard -z -- . ':!reports' ':!.venv' | xargs -0 -I{} cp --parents {} "$copy/"
done
for n in 1 2 3 4; do
    (cd "$work/$label-$n" && exec cosmic-ray http-worker --port "980$n" > "$work/$label-worker$n.log" 2>&1) &
    pids+=($!)
done

cd "$work/$label-0" || exit 1
# MODULES (optional): space separated files to mutate instead of the whole list.
python -I "$repo/tools/mutation/make_config.py" "$repo/tools/mutation/cosmic-ray.toml" "$interpreter"     "$work/$label-resolved.toml" "$work/$label-local.toml" ${MODULES:-} || exit 1
config="$work/$label-resolved.toml"
session="$out/$label.sqlite"
rm -f "$session"
echo "revision $(git -C "$repo" rev-parse HEAD)" > "$out/$label.revision.txt"
git -C "$repo" status --short >> "$out/$label.revision.txt"
cosmic-ray baseline "$work/$label-local.toml" || { echo "baseline failed: tests do not pass unmutated"; exit 1; }
echo "baseline passed"
for n in 1 2 3 4; do
    for attempt in $(seq 1 60); do
        (exec 3<>"/dev/tcp/127.0.0.1/980$n") 2>/dev/null && break
        [ "$attempt" = 60 ] && { echo "worker $n is not listening"; exit 1; }
        sleep 1
    done
done
echo "workers ready"
cosmic-ray init "$config" "$session" || exit 1
echo "mutants: $(cosmic-ray dump "$session" | wc -l)"
date
cosmic-ray exec "$config" "$session" || exit 1
date
cosmic-ray dump "$session" > "$out/$label.dump.jsonl"
cr-report "$session" --show-diff --surviving-only > "$out/$label.survivors.txt"
cr-rate "$session" > "$out/$label.survival-rate.txt"
echo "survival rate: $(cat "$out/$label.survival-rate.txt")"

# MIN_KILL (optional): fail when the kill rate in percent is lower.
python -I "$repo/tools/mutation/summarise.py" "$out/$label.dump.jsonl" "${MIN_KILL:-0}" | tee "$out/$label.summary.txt"
verdict=${PIPESTATUS[0]}

# The copies must end unmutated.
cd "$repo" || exit 1
for n in 0 1 2 3 4; do
    for f in transactions/services.py transactions/loyalty.py store/models.py accounts/permissions.py; do
        cmp -s "$f" "$work/$label-$n/$f" || echo "WARNING: $label-$n/$f differs from the repository"
    done
done
echo "done, verdict $verdict (0 ok, 1 infrastructure errors, 2 kill rate too low)"
exit "$verdict"
