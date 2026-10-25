# qg-l9-runs

GitHub Actions batches for the L9 ringdown (pyRing) analysis. The pipeline code and run configs are byte-identical
copies of the QG team's working tree. Analysis settings and package versions are fixed by the pre-registration and
errata, so do **not** edit `code/`, `runs/*/configs/*.ini`, `pe/` or `requirements.lock.txt` here.

## What runs
* **Environment:** Python 3.11 + `requirements.lock.txt`, frozen from the analysis venv (pyRingGW 2.11.2,
  cpnest 0.12.0, lalsuite 7.26.16, gwpy 4.1.0, gwosc 0.8.3, scikit-learn 1.9.1, ...). Installed with uv; pyRingGW
  builds from its sdist (~1 min).
* **Absolute-path mirroring:** the configs and scripts hard-code `/workspace/qg-unification/l9-run/...` (the QG
  machine's layout). Instead of editing them, CI symlinks the checkout to that path
  (`.github/actions/setup-l9`), so every config and script runs unmodified. Those paths therefore appear in the public
  files and logs; they are a directory layout, not credentials. To run locally elsewhere, create the same symlink.
* **Inputs:** none are committed. A `prep` job per event runs `code/preprocess.py runs/prepcfg/configs/<event>_GR.ini`.
  This downloads public GWOSC 16 kHz strain and writes `prep/<event>/ACF_<IFO>.txt` and `strain64_<IFO>.txt`. The
  outputs are cached and passed to the run jobs as `prep-<event>` artifacts.
* **Sampling:** `code/run_one.sh <config>`. Each run uses 1 thread and ~1 GB RSS. 4 runs are packed per 4-vCPU
  runner; `run-type=full` configs go 2 per runner because pyRing post-processing peaks at ~6.4 GB.
* **Not done here:** `combine.py` (the QG team runs it locally on the downloaded results) and the pyRing 1.0.0
  attribution runs.

## Dispatch
| goal | command |
|---|---|
| **Pilot**: rerun 3 finished box runs with their exact n2048 configs (seed 1234, nlive=maxmcmc=2048, poolsize 128) | `gh workflow run l9-batch.yml -f preset=pilot` |
| **Checkpoint test**, step 1: GW190408_181802_GR, SIGTERM after 20 min | `gh workflow run l9-batch.yml -f preset=pilot-ckpt -f force_checkpoint_min=20` |
| **Checkpoint test**, step 2: resume that run | `gh workflow run l9-batch.yml -f preset=pilot-ckpt -f resume_run_id=<run id of step 1>` |
| Cheap smoke test (nlive 256, 3 runs) | `gh workflow run l9-batch.yml -f preset=smoke` |
| Self-hosted runner (recommended for production) | add `-f runner=<self-hosted label>` to any of the above |
| Any batch / subset | `gh workflow run l9-batch.yml -f preset=custom -f tag=n2048 -f filter='^GW1508' -f runs_per_job=4 -f max_parallel=20` |

Pilot details:
* The pilot uses the n2048 configs exactly as they are, including `run-type=full` for GW150914_GR and GW170104_GR.
* `ci/reference/pilot_box_n2048.json` holds the box results for the three runs. The collect job prints a CI-vs-box
  table: ΔlnZ, ΔlnB in units of √2·√(H/nlive) ≈ 0.09, and whether `posterior.dat` is byte-identical.
* Bitwise identity across different CPUs is not expected. Agreement within ~3σ is.

Box reference (n2048, `Nested_sampler/Evidence.txt`):

| run | lnZ_noise | lnZ_signal | lnB | SNR | H | box wall_s | box exit |
|---|---|---|---|---|---|---|---|
| GW150914_GR | 38753.11669985916 | 38768.31894044798 | 15.202240588820132 | 7.3183 | 8.84 | 3100 | 247 (post-proc OOM after sampling) |
| GW170104_GR | 38866.37022261732 | 38874.12805453094 | 7.757831913622795 | 6.2776 | 8.81 | 4127 | 247 (post-proc OOM after sampling) |
| GW190408_181802_GR | 39451.43272057666 | 39451.73283339049 | 0.3001128138275817 | 4.8598 | 8.16 | 5085 | 0 |

## Limits and checkpoint/resume
GitHub-hosted jobs are killed at 6 h, and the matrix is capped at 256 jobs per dispatch. Split larger batches with
`filter`.

How a long run is carried across jobs:
1. After `run_limit_min` (default 330), or `force_checkpoint_min` for runs matching the forced-checkpoint regex, the
   workflow sends SIGTERM to that run's pyRing processes.
2. cpnest writes `Nested_sampler/nested_sampler_resume.pkl` and `sampler_*.pkl`, then exits with 130.
3. The run directory is uploaded as `partial-<tag>-<job>`.
4. Re-dispatch the same runs with `resume_run_id=<that run id>`. pyRing (`resume=1`) continues from the checkpoint.
5. The interrupted attempt's log and provenance are kept as `logs/<tag>/<run>.attempt-<id>.{log,json}`.

Resume is statistically, not bitwise, equivalent. In a local test (GW150914_GR, nlive=256, SIGTERM after 100 s, resumed):
* the resumed run gave lnB 14.600 (H 9.37);
* two uninterrupted nlive=256 runs gave 15.205 and 15.295 (H 8.7);
* that is ~-0.6, about 3 sigma at nlive=256.

Validate with the `pilot-ckpt` comparison at nlive=2048 before relying on resumed runs.

## Provenance (every run directory)
`runs/<tag>/<run>/provenance.json` records:
* seed, run-type, nlive, maxmcmc, poolsize, nthreads;
* the config path and its sha256;
* commit SHA, workflow run/attempt, runner image + version, CPU;
* Python version and the full package freeze;
* exit code, wall time, peak RSS, timeout and resume flags, and previous attempts;
* lnZ/lnB/SNR, cpnest information, and sha256 of `Evidence.txt`, `posterior.dat` and `cpnest.log`;
* for each event, the prep provenance (`prep/<event>/prep_provenance.json`): every GWOSC URL downloaded with its
  sha256, and the sha256 of each produced ACF/strain file compared against the box hashes in
  `ci/reference/box_prep_sha256.json` and `box_gwosc_sha256.json`.

The full `Nested_sampler/` (`cpnest.log`, `Evidence.txt`, `posterior.dat`, ...) is kept in each result artifact.

## Fetch results
```bash
gh run list --workflow l9-batch.yml
ci/pull_results.sh <run-id>                  # l9-<tag>-merged -> /workspace/qg-l9-staging/<run-id>/ + MANIFEST.sha256
ci/pull_results.sh <run-id> Macrolol/qg-l9-runs all   # every artifact (prep, per-job results, checkpoints)
```
The pull script never writes into `/workspace/qg-unification/`. It refuses an existing destination and makes the
staged copy read-only.

## Layout
* `code/`: pipeline scripts (verbatim).
* `pe/event_params.json`.
* `runs/n2048/configs`: production configs.
* `runs/prepcfg/configs`: preprocessing configs.
* `runs/ci_smoke256/configs`: identical to n2048 except nlive=maxmcmc=256, sampling-only, and the output path.
* `ci/plan.py`: builds the job matrix.
* `ci/prep_provenance.py`, `ci/provenance.py`: write the provenance records.
* `ci/collect.py`: writes `summary.csv`/`summary.json`.
* `ci/compare_reference.py`: the CI-vs-box comparison.
* `ci/pull_results.sh`: downloads results into staging.
* `ci/reference/`: box hashes and pilot reference values.
* `.github/workflows/l9-batch.yml`, `.github/actions/setup-l9`.

## Usage policy
GitHub's Actions terms
(https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features#actions)
forbid, on GitHub-hosted runners, "any other activity unrelated to the production, testing, deployment, or
publication of the software project associated with the repository".

The hosted-runner default is therefore meant for the **pilot, smoke and checkpoint tests of this pipeline only**.
Run production batches with `runner=<self-hosted label>`.
