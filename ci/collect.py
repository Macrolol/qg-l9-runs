"""Merge per-run outputs downloaded from the run jobs into one summary (CI helper; reads outputs only,
does NOT run code/combine.py -- the QG team runs that themselves on the merged tree).
Usage: python ci/collect.py TAG  -> runs/<TAG>/summary.csv, summary.json, and a Markdown table on stdout"""
import csv, glob, json, os, re, sys
tag = sys.argv[1]; R = f'runs/{tag}'
rows = []
for cfg in sorted(glob.glob(f'{R}/configs/*.ini')):
    name = os.path.basename(cfg)[:-4]
    if not (os.path.isdir(f'{R}/{name}') or os.path.exists(f'logs/{tag}/{name}.log')): continue   # not in this dispatch
    row = dict(run=name, status='missing', lnZ_noise='', lnZ_signal='', lnB='', SNR='', wall_s='', maxrss_MB='', exit='',
               resumed=os.path.exists(f'logs/{tag}/{name}.resumed'))
    ev = f'{R}/{name}/Nested_sampler/Evidence.txt'
    if os.path.exists(ev):
        v = open(ev).read().split('\n')[1].split()
        row.update(lnZ_noise=v[0], lnZ_signal=v[1], lnB=v[2], SNR=v[3], status='ok')
    lg = f'logs/{tag}/{name}.log'
    if os.path.exists(lg):
        t = open(lg, errors='replace').read()
        m = re.findall(r'exit=(\d+) wall_s=(\d+)', t); r = re.findall(r'maxrss_children_MB ([\d.]+)', t)
        if m: row.update(exit=m[-1][0], wall_s=m[-1][1])
        if r: row['maxrss_MB'] = f'{float(r[-1]):.0f}'
        if row['status'] == 'missing': row['status'] = 'failed'
        if os.path.exists(f'logs/{tag}/{name}.timeout'): row['status'] += '+timeout'
    rows.append(row)
if not rows: print(f'no runs found for {tag}'); sys.exit(1)
with open(f'{R}/summary.csv', 'w', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
json.dump(rows, open(f'{R}/summary.json', 'w'), indent=1)
ok = sum(r['status'] == 'ok' for r in rows)
print(f'### L9 batch `{tag}`: {ok}/{len(rows)} runs with Evidence.txt\n')
print('| run | status | lnB | SNR | wall_s | maxrss_MB | exit | resumed |\n|---|---|---|---|---|---|---|---|')
for r in rows: print(f"| {r['run']} | {r['status']} | {r['lnB'][:8]} | {r['SNR'][:6]} | {r['wall_s']} | {r['maxrss_MB']} | {r['exit']} | {r['resumed']} |")
print('\nexit 247/137 with status ok = sampling finished, pyRing post-processing was killed (run-type=full); Evidence/posterior are complete.')
sys.exit(0 if ok == len(rows) else 1)
