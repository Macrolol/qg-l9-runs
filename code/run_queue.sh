#!/bin/bash
# Phase-1 validation queue: for each event (in EVENTS order) wait until its preprocessing (code/run_prep_all.sh) is done,
# then run GR and nGRA with code/run_one.sh. At most MAXJ pyRing runs at once (each ~1 GB RSS, 1 core in short-data mode;
# serial preprocessing needs ~5 GB + 1 core alongside).
TAG=${1:-n2048}; MAXJ=${2:-6}; R=/workspace/qg-unification/l9-run
Q=$R/logs/queue_$TAG.log
EVS=$($R/.venv/bin/python -c "import sys; sys.path.insert(0,'$R/code'); from events import EVENTS; print(' '.join(EVENTS))")
for ev in $EVS; do
  until grep -q "^$ev exit=0" $R/logs/prep/ALL.log 2>/dev/null || [ "$ev" = GW150914 ]; do
    if grep -q "^$ev exit=[1-9]" $R/logs/prep/ALL.log 2>/dev/null; then echo "$(date -Is) $ev PREP FAILED - skipped" >> $Q; continue 2; fi
    sleep 20; done
  for m in GR nGRA; do
    while [ $(jobs -rp | wc -l) -ge $MAXJ ]; do wait -n; done
    [ -f $R/logs/$TAG/${ev}_$m.log ] && continue   # already started/done
    echo "$(date -Is) start ${ev}_$m" >> $Q
    bash $R/code/run_one.sh $R/runs/$TAG/configs/${ev}_$m.ini &
  done
done
wait; echo "$(date -Is) QUEUE DONE" >> $Q
