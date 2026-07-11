# BLOCKED

Created UTC: 2026-07-11T04:41:06+00:00

## Stop reason

The study is blocked at the Phase 1 data-contract gate. The ECAL/HCAL hit branches are readable, but
no authoritative evidence was found for the hit-signal meaning or the conversion of `ecal_energy` and
`hcal_energy` to GeV.

## Failing check

`AGENT_PROMPT.md` Phase 1 requires ECAL/HCAL hit-signal meaning and GeV conversion from authoritative
simulation metadata, simulation code, or data documentation. It explicitly forbids resolving the
scale by whichever convention produces better ML results. `docs/MASTER_QC_CHECKLIST.md` item 14
requires locked hit-signal policies before modeling.

## What was resolved

- ROOT object: `gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root`
- GCS object size: 25,022,001,408 bytes, CRC32C `lCVUvQ==`.
- Existing prior Vertex fingerprint for the same object: SHA-256
  `b7c666040e42352e158a9a3f78158d147cb2e056c6c88248d892c956f5c7b533`.
- Latest tree: `myTree;865`, 764,940 entries. Prior cycle `myTree;864` has 764,640 entries and was
  not used.
- Truth-only full pass: `mcPar_length_counts={"1": 764940}`, `flat_pdg_counts={"2112": 764940}`.
  Primary-neutron identity is therefore resolved by the verified single-candidate rule, not by
  "first neutron".
- Truth total-energy semantics are resolved by mass-shell closure: median relative residual
  `7.73733035177439e-17`, p99 `2.8347701735281425e-16`, max `5.129467402495768e-16`; energy range
  `0.939619280394676` to `300.001371033516` GeV.

## Evidence that the hit-unit gate failed

- ROOT tree title is only `MyTree`.
- Branch titles are only names, including `ecal_energy`, `hcal_energy`, `energySum_ecal`,
  `energySum_hcal`, and `energySum_ZDC`; no units, thresholds, digitization semantics, calibration
  constants, sampling fraction, or conversion rule are embedded.
- Histogram axes for ECAL/HCAL position objects have numeric ranges but no axis titles or unit labels.
- Bucket search found no simulation source, detector macro, README, data dictionary, DD4hep/Geant
  code, or other unit authority. The only code object found was a prior diagnostics script:
  `gs://asiop-zdc-1-zdc-reco-us-central1/runs/loss-curves-20260711/code/vertex_loss_curves.py`.
- Prior GCS run artifacts set `hit_signal_scale_to_gev: {ecal: 1.0, hcal: 1.0}`, but they do not
  cite authoritative simulation metadata/code. Under the current prompt, that is insufficient.

## Commands and artifacts

- Metadata CLI: `python -m zdc_hybrid.cli preflight --config configs/study.yaml --data
  gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root
  --output-dir outputs` returned nonzero intentionally and wrote this blocker.
- ROOT metadata: `outputs/preflight/root_metadata.json`.
- Truth summary: `outputs/reports/truth_summary.json`.
- Hit sample summary: `outputs/reports/hit_sample_summary.json`.
- GCS object metadata: `outputs/reports/gcs_object_metadata.txt`.
- QA ledger: `outputs/reports/qa_ledger.md`.

## Smallest decision needed

Provide authoritative documentation or source code that states what `ecal_energy` and `hcal_energy`
represent and the conversion to GeV for absolute energy reconstruction. After that, rerun:

```bash
zdc-reco run-all --config configs/study.yaml --data gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root
```

No feature production, model training, calibration, test unlock, final test metric, champion claim, or
Vertex spend is valid until this blocker is resolved.
