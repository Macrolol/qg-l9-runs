"""Record the provenance of one event's preprocessing (runs on the CI runner, inside .venv, after code/preprocess.py).
Usage: python ci/prep_provenance.py <event>
Writes prep/<event>/prep_provenance.json:
  - every GWOSC file in the astropy download cache (URL, sha256, bytes); on a fresh runner that is exactly what
    preprocess.py downloaded for this event,
  - sha256 of the produced ACF_<IFO>.txt / strain64_<IFO>.txt,
  - comparison of both against the box reference hashes in ci/reference/."""
import sys, os, json, hashlib, glob, datetime
ev = sys.argv[1]
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()
ref_prep = json.load(open('ci/reference/box_prep_sha256.json'))
ref_raw = json.load(open('ci/reference/box_gwosc_sha256.json'))
raw = []
try:
    from astropy.utils.data import cache_contents
    for url, path in sorted(cache_contents().items()):
        if 'gwosc' not in url: continue
        h = sha(path); r = ref_raw.get(url)
        raw.append(dict(url=url, sha256=h, bytes=os.path.getsize(path),
                        box_sha256=r['sha256'] if r else None,
                        matches_box=(r['sha256'] == h) if r else None))
except Exception as x:
    raw.append(dict(error=repr(x)))
prep = []
for p in sorted(glob.glob(f'prep/{ev}/ACF_*.txt') + glob.glob(f'prep/{ev}/strain64_*.txt')):
    h = sha(p); r = ref_prep.get(p)
    prep.append(dict(file=p, sha256=h, bytes=os.path.getsize(p),
                     box_sha256=r['sha256'] if r else None, matches_box=(r['sha256'] == h) if r else None))
out = dict(event=ev, created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
           commit=os.environ.get('GITHUB_SHA'), workflow_run=os.environ.get('GITHUB_RUN_ID'),
           runner_image=f"{os.environ.get('ImageOS')} {os.environ.get('ImageVersion')}",
           prep_config=f'runs/prepcfg/configs/{ev}_GR.ini', prep_config_sha256=sha(f'runs/prepcfg/configs/{ev}_GR.ini'),
           gwosc_inputs=raw, prep_outputs=prep,
           all_prep_match_box=all(x['matches_box'] for x in prep) if prep else False)
json.dump(out, open(f'prep/{ev}/prep_provenance.json', 'w'), indent=1)
print(json.dumps({k: out[k] for k in ('event', 'all_prep_match_box')}),
      *(f"{x['file']} match_box={x['matches_box']}" for x in prep), sep='\n')
