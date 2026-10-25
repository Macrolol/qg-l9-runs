#!/bin/bash
# Fetch public IMR PE samples used only to fix t_peak, sky position and M_f for t0 (Laghi Sec 3.4).
set -e
cd /workspace/qg-unification/l9-run/pe
for e in GW190408_181802 GW190512_180714 GW190519_153544 GW190521 GW190521_074359 GW190602_175927 GW190630_185205 GW190706_222641 GW190708_232457 GW190727_060333 GW190814 GW190828_063405 GW190910_112807 GW190915_235702; do
  [ -d $e ] || { curl -sL -o $e.tar https://dcc.ligo.org/public/0169/P2000223/007/$e.tar && tar xf $e.tar && rm $e.tar; echo got $e; }
done
for e in GW150914_095045 GW170104_101158 GW170608_020116 GW170729_185629 GW170818_022509 GW170823_131358; do
  f=IGWN-GWTC2p1-v2-${e}_PEDataRelease_mixed_cosmo.h5
  [ -f $f ] || { curl -sL -o $f https://zenodo.org/api/files/ecf41927-9275-47da-8b37-e299693fe5cb/$f; echo got $e; }
done
