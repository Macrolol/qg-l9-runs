"""Per-event analysis settings for the L9 phase-1 validation, following Laghi et al. 2021 (arXiv:2011.03816) Sec. 3.4:
  * sky position fixed to the maximum-likelihood IMR sample (ra, dec)
  * t0 = t_peak + 10 M_f, where t_peak is the peak of h+^2 + hx^2 "computed using median values" of the IMR analysis
  * M_f = median detector-frame remnant mass of the IMR analysis
  * LIGO detectors only (Laghi Sec. 3.3/5: Advanced LIGO data)
IMR samples: GWTC-2.1 PE release, group C01:IMRPhenomXPHM, for all 20 events (deviation: Laghi used GWTC-1/GWTC-2/TGR-O3a samples;
the GWTC-2 PublicationSamples have time marginalised out for most events, and GWTC-1 samples carry no time/likelihood).
t_peak in the reference detector = median(<ref>_time) + Delta, where Delta is the time of max(h+^2+hx^2) of the IMRPhenomXPHM
frequency-domain waveform at median parameters, relative to the waveform's own t=0 (= the PE time reference).
Validated on GW150914: gives H1 1126259462.42317 vs pyRing's reference trigtime 1126259462.42323 (0.05 ms).
"""
import json, sys, numpy as np, h5py, lal, lalsimulation as ls
sys.path.insert(0, '/workspace/qg-unification/l9-run/code')
from events import EVENTS
FULL = {"GW150914":"GW150914_095045","GW170104":"GW170104_101158","GW170608":"GW170608_020116","GW170729":"GW170729_185629",
        "GW170818":"GW170818_022509","GW170823":"GW170823_131358","GW190521":"GW190521_030229","GW190814":"GW190814_211039",
        "GW190828_060333":"GW190828_063405"}   # last entry: Laghi Table 2 typo, see NOTES.md
GROUP = 'C01:IMRPhenomXPHM'

def fd_peak_offset(s, apx='IMRPhenomXPHM', fref=20., flow=20., fmax=2048., T=64.):
    med = lambda k: float(np.median(s[k])) if k in s.dtype.names else 0.0
    if 'f_ref' in s.dtype.names: fref = med('f_ref')
    hp, hc = ls.SimInspiralChooseFDWaveform(med('mass_1')*lal.MSUN_SI, med('mass_2')*lal.MSUN_SI,
        med('spin_1x'), med('spin_1y'), med('spin_1z'), med('spin_2x'), med('spin_2y'), med('spin_2z'),
        1e6*lal.PC_SI*med('luminosity_distance'), med('iota'), med('phase'), 0, 0, 0, 1./T, flow, fmax, fref, None,
        ls.GetApproximantFromString(apx))
    n = int(round(2*fmax*T)); a = np.fft.irfft(hp.data.data, n=n)**2 + np.fft.irfft(hc.data.data, n=n)**2
    t = np.argmax(a)/(2*fmax)
    return t if t < T/2 else t - T

if __name__ == '__main__':
    out = {}
    for ev in (sys.argv[1:] or EVENTS):
        full = FULL.get(ev, ev)
        f = h5py.File(f'/workspace/qg-unification/l9-run/pe/IGWN-GWTC2p1-v2-{full}_PEDataRelease_mixed_cosmo.h5', 'r')
        s = f[GROUP]['posterior_samples'][()]
        ifos = [d for d in ('H1','L1') if f'{d}_time' in s.dtype.names]   # LIGO detectors used in the IMR analysis
        ref = ifos[0]
        i = int(np.argmax(s['log_likelihood']))
        mf = s['final_mass'] if 'final_mass' in s.dtype.names else s['final_mass_source']*(1+s['redshift'])
        Mf = float(np.median(mf)); dpk = fd_peak_offset(s)
        tpk = float(np.median(s[f'{ref}_time'])) + dpk
        out[ev] = dict(gwosc_name=full, pe_file=f.filename.split('/')[-1], pe_group=GROUP, detectors=ifos, ref_det=ref,
                       ra_maxL=float(s['ra'][i]), dec_maxL=float(s['dec'][i]), median_ref_time=float(np.median(s[f'{ref}_time'])),
                       peak_offset_s=dpk, trigtime_refdet=tpk, Mf_det_median=Mf, Mf_det_90upper=float(np.percentile(mf,95)),
                       af_median=float(np.median(s['final_spin'])), tM_s=Mf*lal.MTSUN_SI, fix_t=10*Mf*lal.MTSUN_SI,
                       redshift_median=float(np.median(s['redshift'])))
        print(ev, ifos, ref, f'tpk={tpk:.5f} off={1e3*dpk:.2f}ms Mf={Mf:.1f} af={out[ev]["af_median"]:.2f} fix_t={1e3*out[ev]["fix_t"]:.2f}ms', flush=True)
    fn = '/workspace/qg-unification/l9-run/pe/event_params.json'
    try: old = json.load(open(fn))
    except Exception: old = {}
    old.update(out); json.dump(old, open(fn,'w'), indent=1)
