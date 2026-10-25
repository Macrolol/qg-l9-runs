"""Pre-populate gwpy/astropy download cache with public GWOSC strain (16 kHz, as pyRing's download-data path requests)
for the LIGO detectors of Laghi's 20 events. pyRing later calls TimeSeries.fetch_open_data(..., cache=True) and hits this cache."""
import sys, time
from gwpy.timeseries import TimeSeries
from gwosc.datasets import event_gps
sys.path.insert(0,'code'); from events import EVENTS
ALIAS={"GW190828_060333":"GW190828_063405"}
DETS={"GW190630_185205":["L1"],"GW190708_232457":["L1"],"GW190910_112807":["L1"],"GW170608":["H1","L1"]}
T=4096.
for ev in (sys.argv[1:] or EVENTS):
    n=ALIAS.get(ev,ev); g=event_gps(n)
    for d in DETS.get(n,["H1","L1"]):
        t=time.time()
        try:
            ts=TimeSeries.fetch_open_data(d,int(g)-T/2-2,int(g)+T/2+2,sample_rate=16384,cache=True,verbose=False)
            print(ev,d,'ok',ts.duration, f'{time.time()-t:.0f}s', 'nan' if (ts.value!=ts.value).any() else 'finite', flush=True)
        except Exception as x: print(ev,d,'FAIL',repr(x)[:200],flush=True)
