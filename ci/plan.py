"""Split runs/<TAG>/configs/*.ini into GitHub Actions matrix jobs (CI helper; no analysis logic).
Each run is single-threaded (nthreads=1), so a 4-vCPU runner takes RUNS_PER_JOB=4 runs side by side.
Configs with run-type=full (pyRing full post-processing, ~6.4 GB RSS, see NOTES) are packed at most 2 per job
so they fit in the runner's 16 GB.
Usage: python ci/plan.py TAG RUNS_PER_JOB [REGEX]  -> writes matrix=..., events=..., n_runs=..., n_jobs=... to $GITHUB_OUTPUT"""
import glob, json, os, re, sys
tag, rpj = sys.argv[1], int(sys.argv[2])
rx = re.compile(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] else None
cfgs = sorted(glob.glob(f'runs/{tag}/configs/*.ini'))
if rx: cfgs = [c for c in cfgs if rx.search(os.path.basename(c))]
if not cfgs: sys.exit(f'no configs matched in runs/{tag}/configs')
def info(c):
    txt = open(c).read()
    evs = sorted(set(re.findall(r'^(?:data|acf)-[HLV]1=.*/prep/([^/]+)/', txt, re.M)))
    if not evs: sys.exit(f'{c}: not a short-data (L9PREP=1) config; the CI pipeline only runs the low-memory mode')
    full = re.search(r'^run-type=full$', txt, re.M) is not None
    return os.path.basename(c), evs, full
runs = [info(c) for c in cfgs]
jobs = []
for full in (False, True):
    sel = [r for r in runs if r[2] == full]
    k = min(rpj, 2) if full else rpj
    for i in range(0, len(sel), k):
        ch = sel[i:i+k]
        jobs.append(dict(id=f'j{len(jobs):03d}', configs=' '.join(r[0] for r in ch),
                         events=' '.join(sorted({e for r in ch for e in r[1]})), n=len(ch)))
if len(jobs) > 256: sys.exit(f'{len(jobs)} jobs > 256 (GitHub matrix limit): raise RUNS_PER_JOB or split with REGEX')
events = sorted({e for r in runs for e in r[1]})
out = dict(matrix=json.dumps({'include': jobs}), events=json.dumps(events), n_runs=len(runs), n_jobs=len(jobs))
with (open(os.environ['GITHUB_OUTPUT'], 'a') if 'GITHUB_OUTPUT' in os.environ else sys.stdout) as f:
    for k, v in out.items(): f.write(f'{k}={v}\n')
print(f'{len(runs)} runs -> {len(jobs)} jobs, {len(events)} events', file=sys.stderr)
