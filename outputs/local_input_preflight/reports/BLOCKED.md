# BLOCKED

Created UTC: 2026-07-11T05:33:58+00:00

## Stop reason

Authoritative ECAL/HCAL hit-signal unit evidence was not supplied or found.

## Failing check

`docs/MASTER_QC_CHECKLIST.md` item 14 and `AGENT_PROMPT.md` Phase 1 require authoritative
ECAL/HCAL hit-signal meaning and GeV conversion from simulation metadata, simulation code, or data
documentation. The ROOT file branch titles expose only names such as `ecal_energy` and
`hcal_energy`; no units, thresholds, digitization semantics, or conversion rule are embedded.

## Evidence

- Input data URI: `C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all 1\myTree_20251117_765k_0to300GeV_neutron_All.root`
- Metadata report: `outputs\local_input_preflight\preflight\root_metadata.json`
- ROOT metadata can be opened, but the metadata fields and histogram axes contain no hit-signal unit
  evidence.
- The repository and bucket search found no simulation source, detector macro, README, or data
  dictionary that defines `ecal_energy`/`hcal_energy` units.

## Smallest decision needed

Provide authoritative documentation or source code that states what `ecal_energy` and `hcal_energy`
represent and the conversion to GeV for absolute energy reconstruction. After that, rerun:

```bash
zdc-reco run-all --config configs/study.yaml --data C:\Users\Julia\OneDrive\Desktop\coding\ASIoP\ML ZDC all 1\myTree_20251117_765k_0to300GeV_neutron_All.root
```

No training, calibration, test unlock, or performance claim is valid until this blocker is resolved.
