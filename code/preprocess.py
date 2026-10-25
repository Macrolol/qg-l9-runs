"""Per-event noise preprocessing, done ONCE per event and shared by all models (GR, nGR_A, ...).
Runs pyRing's own data-conditioning + ACF estimator (noise.load_data) on 4096 s of GWOSC strain exactly as a
`download-data=1, datalen-download=4096` pyRing run would (4 s chunks, chunk containing the trigger excluded,
Butterworth bandpass [20,2043] Hz, 4096 Hz), writes the ACF file, and writes a short 64 s raw 16 kHz strain file
around the trigger. Sampling runs then use acf-<IFO>=<ACF file> + data-<IFO>=<short file>; this cuts per-run RAM
from ~4 GB to well under 1 GB so 8 runs fit in parallel. Equivalence checked on GW150914 (see NOTES.md).
Usage: python preprocess.py <GR config .ini>"""
import sys, os, configparser, numpy as np
from pyRing import initialise, noise
from gwpy.timeseries import TimeSeries
cfg = sys.argv[1]
C = configparser.ConfigParser(); C.read(cfg)
ev = os.path.basename(cfg).rsplit('_',1)[0]
R = '/workspace/qg-unification/l9-run'
outdir = f'{R}/prep/{ev}'; os.makedirs(outdir, exist_ok=True)
C.set('input','output', outdir)
tmp = f'{outdir}/prep.ini'; C.write(open(tmp,'w'))
ip = initialise.read_config(C, tmp, print_params=0)
initialise.create_directories(ip['output'])
trig = ip['trigtime']
for ifo in ip['detectors']:
    noise.load_data(ifo, '', **ip)
    # pyRing names the ACF after the (possibly NaN-resized) data start/length -> glob; exactly one must exist
    import glob
    acfs = glob.glob(f"{outdir}/Noise/ACF_{ifo}_*_{ip['noise-chunksize']}_{ip['sampling-rate']}.txt")
    assert len(acfs) == 1, acfs
    acf = acfs[0]; print('ACF from', os.path.basename(acf), flush=True)
    os.replace(acf, f'{outdir}/ACF_{ifo}.txt')
    ts = TimeSeries.fetch_open_data(ifo, int(trig)-32, int(trig)+32, sample_rate=16384, cache=True)
    assert np.all(np.isfinite(ts.value)), f'NaNs in short data {ev} {ifo}'   # never let NaNs reach the likelihood
    np.savetxt(f'{outdir}/strain64_{ifo}.txt', np.column_stack((ts.times.value, ts.value)))
    print('done', ev, ifo, flush=True)
