# MC ROOT delivery index

This delivery contains no raw ROOT data. The authoritative raw input remains at:

```text
gs://asiop-zdc-1-zdc-reco-us-central1/data/myTree_20251117_765k_0to300GeV_neutron_All.root
```

Read these files in order:

1. `MC_ROOT_VERTEX_QA_LOG.md`: Vertex execution history, failures, fixes, and final acceptance checks.
2. `MC_ROOT_DATA_AND_VERTEX_FASTMC.md`: what the file contains, measured findings, fast-MC limits, and cloud-only access commands.
3. `fast_mc_input_contract_v3.json`: machine-readable fast-MC constraints corrected from the full v3 scan.
4. `cloud_outputs/reports/mc_root_full_analysis.json`: complete numerical report over all 40 vector branches.
5. `cloud_outputs/tables/`: branch catalog, PDG count, jagged alignment checks, and geometry-location tables.
6. `cloud_outputs/plots/`: four Vertex-generated diagnostic figures.
7. `source/` and `vertex/`: the exact reducer source and Cloud Build/Vertex job definitions.

The successful result source is Vertex custom job
`projects/39719277374/locations/us-central1/customJobs/4153478300037021696` and its GCS output
prefix is:

```text
gs://asiop-zdc-1-zdc-reco-us-central1/runs/mc-root-full-analysis-20260713-v3/outputs/
```
