#!/bin/bash
# run code/preprocess.py for all events, SERIALLY (each needs ~5 GB peak while conditioning 4096 s of 16 kHz data;
# two in parallel + other jobs hit the OOM killer on 2026-10-24 14:41 ET). Skips events whose ACF files exist.
R=/workspace/qg-unification/l9-run; source $R/.venv/bin/activate; export MPLBACKEND=Agg OMP_NUM_THREADS=1
mkdir -p $R/logs/prep
for cfg in $R/runs/prepcfg/configs/*_GR.ini; do
  ev=$(basename $cfg _GR.ini); [ -f $R/prep/$ev/strain64_L1.txt ] && continue
  s=$(date +%s); python $R/code/preprocess.py $cfg > $R/logs/prep/$ev.log 2>&1
  echo "$ev exit=$? wall_s=$(( $(date +%s)-s )) $(date -Is)" >> $R/logs/prep/ALL.log
done
echo ALLDONE >> $R/logs/prep/ALL.log
