#!/bin/bash
# run one pyRing config; record wall time + peak RSS
cfg=$1; name=$(basename $cfg .ini); tag=$(basename $(dirname $(dirname $cfg)))
mkdir -p /workspace/qg-unification/l9-run/logs/$tag
source /workspace/qg-unification/l9-run/.venv/bin/activate
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MPLBACKEND=Agg
# short-data mode: pyRing's post-processing SNR plot globs <output>/Noise/ACF_<IFO>_*.txt -> put a copy of the ACF file there
out=$(grep '^output=' $cfg | cut -d= -f2); mkdir -p $out/Noise
for a in $(grep '^acf-[HLV]1=' $cfg); do ifo=$(echo $a | cut -d= -f1 | cut -c5-); cp $(echo $a | cut -d= -f2) $out/Noise/ACF_${ifo}_fromprep.txt; done
start=$(date +%s); python -c "import resource,subprocess,sys; r=subprocess.call(sys.argv[1:]); print(\"maxrss_children_MB\", resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024); sys.exit(r)" pyRing --config-file $cfg > /workspace/qg-unification/l9-run/logs/$tag/$name.log 2>&1
echo "exit=$? wall_s=$(( $(date +%s)-start )) $(date -Is)" >> /workspace/qg-unification/l9-run/logs/$tag/$name.log
