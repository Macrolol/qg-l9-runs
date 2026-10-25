#!/bin/bash
# GWTC-2.1 PE (Zenodo 6513631) for the 14 O3a validation events; IMRPhenomXPHM group used for t_peak/sky/Mf (see NOTES.md)
cd /workspace/qg-unification/l9-run/pe
for e in GW190408_181802 GW190512_180714 GW190519_153544 GW190521_030229 GW190521_074359 GW190602_175927 GW190630_185205 GW190706_222641 GW190708_232457 GW190727_060333 GW190814_211039 GW190828_063405 GW190910_112807 GW190915_235702; do
  f=IGWN-GWTC2p1-v2-${e}_PEDataRelease_mixed_cosmo.h5
  [ -s $f ] || { curl -sfL -o $f "https://zenodo.org/api/records/6513631/files/$f/content" && echo got $e || echo FAIL $e; }
done
