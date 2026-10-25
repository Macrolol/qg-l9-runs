"""Compare CI results with the box reference (ci/reference/pilot_box_<tag>.json). Report-only; always exits 0.
Usage: python ci/compare_reference.py <tag>"""
import sys, os, json, hashlib
tag = sys.argv[1]; ref = f'ci/reference/pilot_box_{tag}.json'
if not os.path.exists(ref): sys.exit(0)
R = json.load(open(ref))['runs']
def sha(p): return hashlib.sha256(open(p, 'rb').read()).hexdigest()
print(f'\n### Box reference comparison ({tag})\n')
print('| run | lnZ_noise CI-box | lnZ_signal CI-box | lnB CI | lnB box | dlnB | dlnB/sigma | posterior identical |')
print('|---|---|---|---|---|---|---|---|')
for r, b in R.items():
    ev = f'runs/{tag}/{r}/Nested_sampler/Evidence.txt'
    if not os.path.exists(ev): print(f'| {r} | not run / unfinished | | | {b["lnB"]:.4f} | | | |'); continue
    v = [float(x) for x in open(ev).read().split('\n')[1].split()]
    post = f'runs/{tag}/{r}/Nested_sampler/posterior.dat'
    same = os.path.exists(post) and sha(post) == b['posterior_sha256']
    d = v[2] - b['lnB']; s = (2 ** 0.5) * b['lnZ_sigma_est']
    print(f'| {r} | {v[0]-b["lnZ_noise"]:+.6f} | {v[1]-b["lnZ_signal"]:+.4f} | {v[2]:.4f} | {b["lnB"]:.4f} | {d:+.4f} | {d/s:+.2f} | {same} |')
print('\nsigma = sqrt(2) * sqrt(H/nlive) from the box cpnest information H; |dlnB/sigma| < 3 is consistent.')
