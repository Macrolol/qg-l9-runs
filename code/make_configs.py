"""Write pyRing (pyRingGW 2.11.2) config files for the L9 phase-1 validation (Laghi et al. 2021 settings).
models: GR   = Kerr 220 (Laghi's GR hypothesis)
        nGRA = area-quantization=1 (pyRing QNM_220_area_quantized: omega0 from Laghi Eq. 6, tau0 = 2 Q_GR/omega0, Eq. 8)
        nGRF = area-quantization=1 + tau-AQ=1 (tau0 free, U[0.5,50] ms as in Laghi Sec. 3.4)  [not needed for phase 1]
Priors: pyRing defaults, which equal Laghi Sec. 3.4: Mf U[10,500], af U[0,0.99], A,A' U[0,50], phi,phi' U[0,2pi], alpha U[0,50],
        logD_L in [ln10, ln1e4] with p(D)~D^2 (dist-flat-prior=0), cosiota U[-1,1] (amp-include-harmonics=1).
L9PREP=1: use prep/<ev>/strain64_<IFO>.txt + ACF_<IFO>.txt from code/preprocess.py (ACF from 4096 s, same estimator).
Usage: python make_configs.py NLIVE MAXMCMC [events...]"""
import json, sys, os
R = '/workspace/qg-unification/l9-run'
P = json.load(open(f'{R}/pe/event_params.json'))
nlive, maxmcmc = int(sys.argv[1]), int(sys.argv[2])
evs = sys.argv[3:] or list(P)
# GW190519_153544 L1: GWOSC has no 16 kHz L1 data at int(trig)-2048 (file starts 1 s later) -> 4094 s (start int(trig)-2047)
# GW170608 H1: same situation (GWTC-1 16 kHz H1 file starts at int(trig)-2047)
DATALEN = {'GW190519_153544': 4094.0, 'GW170608': 4094.0}
TAG = os.environ.get('L9TAG', f'n{nlive}')
RUNTYPE = os.environ.get('L9RUNTYPE', 'full')  # n2048 production: configs not yet started at 15:45 ET patched to sampling-only after a postproc OOM
def cfg(ev, model):
    p = P[ev]; out = f'{R}/runs/{TAG}/{ev}_{model}'
    extra = {'GR':'', 'nGRA':'area-quantization=1\n', 'nGRF':'area-quantization=1\ntau-AQ=1\n'}[model]
    pri = {'GR':'', 'nGRA':'', 'nGRF':'tau_AQ-min=0.0005\ntau_AQ-max=0.05\n'}[model]
    if os.environ.get('L9PREP','0')=='1':
        d = f'{R}/prep/{ev}'
        datablock = 'download-data=0\nignore-data-filename=1\nacf-source=acf-file\n' + ''.join(f'data-{i}={d}/strain64_{i}.txt\nacf-{i}={d}/ACF_{i}.txt\n' for i in p['detectors'])
    else:
        datablock = f'download-data=1\ndatalen-download={DATALEN.get(ev,4096.0)}\n'
    return f"""[input]
run-type={RUNTYPE}
pesummary=0
screen-output=0
output={out}
{datablock}trigtime={p['trigtime_refdet']!r}
detectors={','.join(p['detectors'])}
ref-det={p['ref_det']}
sampling-rate=4096.0
f-min-bp=20.0
f-max-bp=2043.0
noise-chunksize=4.0
signal-chunksize=4.0
analysis-duration=0.1
truncate=1
template=Kerr
kerr-modes=[(2,2,2,0)]
sky-frame=equatorial
reference-amplitude=0.0
amp-include-harmonics=1
{extra}
[Sampler settings]
sampler=cpnest
nlive={nlive}
maxmcmc={maxmcmc}
poolsize=128
nthreads=1
seed=1234
verbose=1

[Priors]
mf-time-prior={p['Mf_det_median']!r}
fix-t={p['fix_t']!r}
fix-ra={p['ra_maxL']!r}
fix-dec={p['dec_maxL']!r}
{pri}
[Injection]

[Plot]
"""
os.makedirs(f'{R}/runs/{TAG}/configs', exist_ok=True)
for ev in evs:
    for m in (os.environ.get('L9MODELS','GR,nGRA').split(',')):
        fn = f'{R}/runs/{TAG}/configs/{ev}_{m}.ini'; open(fn,'w').write(cfg(ev, m)); print(fn)
