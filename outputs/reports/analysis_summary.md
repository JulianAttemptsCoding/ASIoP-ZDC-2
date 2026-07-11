# Blocked Study Summary

## Bottom line

The repository and data were inspected, the local Python 3.11 environment was built, existing tests
were repaired and rerun, and the supplied GCS ROOT file was opened successfully. The study cannot
validly proceed to production features, model training, calibration, or test evaluation because the
ECAL/HCAL hit-signal units are not authoritatively documented.

## Data facts established

- Data URI: `gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root`
- GCS size: 25,022,001,408 bytes.
- Prior Vertex SHA-256 for the same object: `b7c666040e42352e158a9a3f78158d147cb2e056c6c88248d892c956f5c7b533`.
- Latest tree: `myTree;865` with 764,940 entries.
- Branches include ECAL/HCAL hit IDs, positions, and energies plus MC particle momentum/energy.
- Truth-only full pass verified exactly one MC particle per event, all PDG 2112.
- `mcPar_energy` is total energy in GeV by mass-shell closure.

## Why no champion exists

The prompt requires absolute four-vector reconstruction in GeV and explicitly forbids choosing the
hit-energy scale by downstream model performance. ROOT branch titles and histogram axes provide no
unit metadata. The bucket search found no simulation source or data dictionary. Prior run artifacts
assumed a unit scale, but did not provide the required authority. Therefore no model trained from
these hit branches would satisfy the protocol.

## Existing prior Vertex artifacts

The GCS bucket contains prior CPU-only XGBoost artifacts from July 10, 2026. They are useful context
but not accepted as completion for this prompt because they used an older `configs/default.yaml`, did
not include the current fail-closed hit-unit evidence, did not run the required dual-grid T4 path, and
were not generated from the current repository state.

## Reproduction command

After authoritative hit-unit evidence is provided:

```bash
zdc-reco run-all --config configs/study.yaml --data gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root
```

Current command result without that evidence: fail closed with `outputs/reports/BLOCKED.md`.
