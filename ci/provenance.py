"""Write runs/<tag>/<run>/provenance.json for one finished (or checkpointed) run. Runs on the CI runner.
Usage: python ci/provenance.py <config .ini> <freeze.txt>"""
import sys, os, re, json, hashlib, configparser, platform, datetime, glob
cfg, freeze = sys.argv[1], sys.argv[2]
name = os.path.basename(cfg)[:-4]; tag = os.path.basename(os.path.dirname(os.path.dirname(cfg)))
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 22), b''): h.update(b)
    return h.hexdigest()
C = configparser.ConfigParser(); C.read(cfg)
flat = {k: v for s in C.sections() for k, v in C.items(s)}
rundir = f'runs/{tag}/{name}'; ns = f'{rundir}/Nested_sampler'
log = f'logs/{tag}/{name}.log'; L = open(log).read() if os.path.exists(log) else ''
m = re.findall(r'exit=(\d+) wall_s=(\d+)', L); rss = re.findall(r'maxrss_children_MB ([\d.]+)', L)
events = sorted(set(re.findall(r'/prep/([^/]+)/', ' '.join(v for k, v in flat.items() if k.startswith(('data-', 'acf-'))))))
prep = {}
for ev in events:
    p = f'prep/{ev}/prep_provenance.json'
    prep[ev] = json.load(open(p)) if os.path.exists(p) else None
resumed = f'logs/{tag}/{name}.resumed'
prev = []
for p in sorted(glob.glob(f'logs/{tag}/{name}.attempt*.json')): prev.append(json.load(open(p)))
ev_row = None
if os.path.exists(f'{ns}/Evidence.txt'):
    v = open(f'{ns}/Evidence.txt').read().split('\n')[1].split()
    ev_row = dict(lnZ_noise=float(v[0]), lnZ_signal=float(v[1]), lnB=float(v[2]), SNR=float(v[3]))
info = re.findall(r'Information: ([\d.]+)', open(f'{ns}/cpnest.log').read()) if os.path.exists(f'{ns}/cpnest.log') else []
keep = {f: (sha(f'{ns}/{f}') if os.path.exists(f'{ns}/{f}') else None) for f in ('Evidence.txt', 'posterior.dat', 'cpnest.log')}
out = dict(
    run=name, tag=tag, created_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    config=f'runs/{tag}/configs/{name}.ini', config_sha256=sha(cfg),
    seed=flat.get('seed'), run_type=flat.get('run-type'), nlive=flat.get('nlive'), maxmcmc=flat.get('maxmcmc'),
    poolsize=flat.get('poolsize'), nthreads=flat.get('nthreads'),
    commit=os.environ.get('GITHUB_SHA'), repository=os.environ.get('GITHUB_REPOSITORY'),
    workflow_run=os.environ.get('GITHUB_RUN_ID'), workflow_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'),
    job=os.environ.get('L9_JOB_ID'),
    runner=dict(image=os.environ.get('ImageOS'), image_version=os.environ.get('ImageVersion'),
                os=os.environ.get('RUNNER_OS'), arch=os.environ.get('RUNNER_ARCH'), name=os.environ.get('RUNNER_NAME'),
                cpu=next((l.split(':', 1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')), None),
                ncpu=os.cpu_count()),
    python=platform.python_version(), packages=[l.strip() for l in open(freeze) if l.strip()],
    exit_code=int(m[-1][0]) if m else None, wall_s=int(m[-1][1]) if m else None,
    maxrss_children_MB=float(rss[-1]) if rss else None,
    timed_out_this_attempt=os.path.exists(f'logs/{tag}/{name}.timeout'),
    resumed=os.path.exists(resumed), resumed_from=open(resumed).read().strip() if os.path.exists(resumed) else None,
    previous_attempts=prev,
    checkpoint_present=os.path.exists(f'{ns}/nested_sampler_resume.pkl') or bool(glob.glob(f'{rundir}/**/*resume*.pkl', recursive=True)),
    evidence=ev_row, cpnest_information=float(info[-1]) if info else None, output_sha256=keep,
    inputs=prep)
json.dump(out, open(f'{rundir}/provenance.json', 'w'), indent=1)
print(name, 'exit', out['exit_code'], 'wall', out['wall_s'], 'resumed', out['resumed'], 'evidence', ev_row)
