# ZDC MC ROOT data and Vertex fast-MC guide

## Scope

The authoritative raw input is the Cloud Storage object below. It is read directly by a
Vertex AI custom job. This workflow does not require, read, or retain a local copy of the
ROOT file.

```text
gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root
```

The submitted full-file scan is defined by `vertex/mc_root_full_analysis.yaml` and executed
by `zdc_reco.mc_root_analysis`. Its compact results live under this separate prefix:

```text
gs://asiop-zdc-1-zdc-reco-us-central1/runs/mc-root-full-analysis-20260713-v3/outputs/
```

## What the ROOT object represents

Each TTree entry is one simulated ZDC event. The event payload is variable length: every
detector and MC-particle branch is a vector, so the number of hits and particles is allowed
to vary from event to event. The analysis selects the newest `myTree` cycle and records the
available ROOT cycles and histogram objects in its report.

The branch families are:

| Family | Per-entry vectors | Meaning |
|---|---|---|
| ECAL response | `ecal_cellID`, `ecal_energy`, `ecal_posX/Y/Z` | Variable-length ECAL hit deposits with cell identifier and hit center position. |
| HCAL response | `hcal_cellID`, `hcal_LayerID`, `hcal_energy`, `hcal_posX/Y/Z` | Variable-length HCAL hit deposits with both cell and longitudinal layer identifiers. |
| MC truth | `mcPar_*` | Generated-particle identity, mass, momentum, energy, angles, vertices, and end-point quantities. |
| Stored summaries | `energySum_*`, `energyRatio_*` | Per-event summary vectors that are compared against sums calculated from raw hit deposits. |

The file is a simulation response sample, not a digitized detector stream. Its schema has no
timing, waveform, ADC, gain, electronics-noise, or pileup branch. A model trained from it is
therefore a simulation-domain fast MC or reconstruction surrogate, not a real-detector
calibration model.

## Truth convention

For a neutron of mass `m_n = 0.93956542052 GeV`, a physically consistent truth four-vector
obeys:

```text
E_total = sqrt(px^2 + py^2 + pz^2 + m_n^2)
T = E_total - m_n
theta = arccos(pz / |p|)
phi = atan2(py, px)
```

Do not infer whether `mcPar_energy` is total or kinetic energy from its name. The Vertex
reducer tests total-versus-kinetic and GeV-versus-MeV candidates against the mass shell over
the full sample, then writes the accepted convention and residual statistics to
`reports/mc_root_full_analysis.json`. A fast-MC generator should condition on the canonical
`E_total`, `T`, `px`, `py`, `pz`, `theta`, and `phi` produced by that check.

## Fast-MC target

The minimal conditional model is:

```text
p(response | E_total, px, py, pz)
```

where `response` may be represented at one of three compatible levels:

1. Response level: ECAL and HCAL deposited-energy totals, hit counts, and shower moments.
2. ECAL grid level: a nonnegative `20 x 20` tensor indexed by `ecal_cellID`.
3. HCAL coordinate-binned level: a tensor made from a documented position-binning rule.
4. Hit level: the original jagged ECAL and HCAL vectors.

For each truth condition, preserve ECAL/HCAL energy correlation, hit multiplicities, cell and
layer occupancy, per-hit nonnegative deposits, zero-hit events, and shower-position structure.
The reducer writes a machine-readable contract at
`reports/fast_mc_input_contract.json`; use that file rather than hard-coding geometry sizes.

The ECAL mapping is validated: all 400 ECAL cell IDs have stable recorded positions and form the
`20 x 20` transverse set. HCAL is different: the full scan found 65 layer IDs and 6,454 observed
`(hcal_LayerID, hcal_cellID)` pairs, but 665,613 position conflicts for those pairs. In other
words, the recorded HCAL positions are hit locations, not a stable cell-center lookup keyed only
by layer and cell ID. Do not claim an ID-derived `64 x 8` HCAL image from this file. Use jagged
hits or define and validate an explicit coordinate binning.

## Vertex v3 full-scan result

Vertex custom job `4153478300037021696` succeeded on 2026-07-13 in `us-central1`. It read the
25,022,001,408-byte GCS object (generation `1783683550292251`), staged it to the worker's
ephemeral SSD in 306.8 seconds, and scanned the latest `myTree` cycle.

| Check | Measured result |
|---|---|
| Entries and branches | 764,940 events; 40 vector branches |
| Truth particle | Exactly one PDG 2112 neutron in every event |
| `mcPar_energy` | Total energy in GeV, not kinetic energy; mass-shell median relative residual `2.52e-12` and p99 `5.70e-9` |
| Energy coverage | total energy `0.9396` to `300.0014` GeV; 509,587 events in 50-250 GeV |
| ECAL deposits | 84,055,028 hits; 109.88 hits/event mean; 56,250 zero-ECAL events |
| HCAL deposits | 1,328,832,592 hits; 1,737.17 hits/event mean; 9,790 zero-HCAL events |
| Zero visible signal | 7,600 events |
| Jagged alignment | 0 mismatches for every ECAL, HCAL, and selected MC-truth branch comparison |
| Stored sum check | ECAL, HCAL, and ZDC differences are zero within floating-point roundoff (largest absolute difference `1.35e-13`) |

The report, branch catalog, geometry tables, and figures in the v3 prefix are the source for
these numbers. The earlier remote-streaming attempt was cancelled before reporting; the second
attempt failed because its 500 MB chunking exhausted worker memory. Neither is a results source.
The current `04_coordinate_centers.png` HCAL panel contains representative first-seen locations
from the full scan. Its original panel title says "centers"; interpret it only through the
665,613-conflict result above. Future runs use the corrected title in the checked-in code.

## Vertex-only access from this computer

The computer only needs Google Cloud authentication and this repository. Do not download the
ROOT object locally.

```powershell
gcloud auth login
gcloud config set project asiop-zdc-1
gcloud storage ls gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root

gcloud builds submit --project=asiop-zdc-1 --region=us-central1 `
  --config=vertex/cloudbuild.mc_root_analysis.yaml --ignore-file=.gcloudignore .

gcloud ai custom-jobs create --project=asiop-zdc-1 --region=us-central1 `
  --display-name=zdc-mc-root-full-analysis-YYYYMMDD `
  --config=vertex/mc_root_full_analysis.yaml
```

Use the custom-job name printed by the last command to monitor the managed worker:

```powershell
gcloud ai custom-jobs describe CUSTOM_JOB_NAME --project=asiop-zdc-1 --region=us-central1
gcloud ai custom-jobs stream-logs CUSTOM_JOB_NAME --project=asiop-zdc-1 --region=us-central1
gcloud storage ls gs://asiop-zdc-1-zdc-reco-us-central1/runs/mc-root-full-analysis-20260713-v3/outputs/**
```

The caller needs permission to submit Vertex jobs and read the input object. The Vertex runtime
service account needs read permission on the input prefix and write permission on the output
prefix. The current job uses an `n1-highmem-32` worker, a 300 GB SSD boot disk, and a 2-hour
timeout. It first stages the GCS object onto that worker's ephemeral SSD, then scans it locally
on the worker with parallel decompression. The raw ROOT object remains in GCS and the temporary
worker copy is removed when the job exits; only the report, tables, plots, and manifest are
written to the output prefix.

## Full-scan deliverables

The completed Vertex job produces:

```text
reports/mc_root_full_analysis.json
reports/fast_mc_input_contract.json
reports/analysis_manifest.json
tables/root_branch_catalog.csv
tables/pdg_counts.csv
tables/jagged_alignment_checks.csv
tables/ecal_cell_centers.csv
tables/hcal_layer_cell_centers.csv
plots/01_event_and_hit_distributions.png
plots/02_signal_response.png
plots/03_raw_response_slices.png
plots/04_coordinate_centers.png
```

Before using the result, list the GCS prefix and check that the alignment table contains zero
mismatches, the stored-versus-calculated energy-sum residuals are zero within floating-point
precision, and the mass-shell convention passed decisively. The job manifest records execution
settings; the job report is the numerical source of truth for event count, branch content, energy
units, geometry coverage, and fast-MC constraints.
