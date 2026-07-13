# MC ROOT Vertex QA log

## Final result

- Final Vertex job: `projects/39719277374/locations/us-central1/customJobs/4153478300037021696`
- State: `JOB_STATE_SUCCEEDED`
- Run window: 2026-07-13 16:01:09 to 16:47:00 UTC
- Input: `gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root`
- Final output: `gs://asiop-zdc-1-zdc-reco-us-central1/runs/mc-root-full-analysis-20260713-v3/outputs/`
- Raw ROOT handling: staged only to the Vertex worker's ephemeral SSD, then deleted with the worker.

## Iterations

| Iteration | Vertex job | Outcome | Action taken |
|---|---|---|---|
| v1 | `1347542218138714112` | Cancelled after an hour of remote random-access ROOT reading without a final report | Stage the GCS object to Vertex SSD before Uproot reads it. |
| v2 | `8639573702293323776` | Failed: Vertex reported worker memory pressure | Bound quantile samples, reduce the chunk from 500 MB to 100 MB, reduce decompression workers, and use a high-memory machine. |
| v3 | `4153478300037021696` | Succeeded | Use as the only result source. |

## v3 acceptance checks

| Check | Result |
|---|---|
| Root entries | 764,940 |
| Branches analyzed | 40 vector branches |
| MC particle identity | 764,940 PDG 2112 particles; exactly one per event |
| Truth energy convention | Total energy in GeV; mass-shell median relative residual `2.52e-12`, p99 `5.70e-9` |
| Jagged-vector lengths | Zero mismatches in all 17 comparisons |
| Stored energy summaries | Recomputed ECAL, HCAL, and ZDC sums agree within `1.35e-13` absolute floating-point roundoff |
| ECAL ID-position mapping | 400 IDs, zero conflicts, valid 20x20 mapping |
| HCAL ID-position mapping | 6,454 layer-cell pairs and 665,613 conflicts; no fixed ID-derived grid claim permitted |
| Raw output hygiene | Redundant worker-staging `input.root` object removed from the v3 output prefix |

## Verification commands

```powershell
gcloud ai custom-jobs describe projects/39719277374/locations/us-central1/customJobs/4153478300037021696 `
  --project=asiop-zdc-1 --region=us-central1

gcloud storage ls gs://asiop-zdc-1-zdc-reco-us-central1/runs/mc-root-full-analysis-20260713-v3/outputs/**

gcloud storage cat gs://asiop-zdc-1-zdc-reco-us-central1/runs/mc-root-full-analysis-20260713-v3/outputs/reports/mc_root_full_analysis.json
```
