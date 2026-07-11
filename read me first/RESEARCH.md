# Research basis and source-to-decision map

The exact detector dimensions come from the user; no external source is used to pretend they describe
a different public ZDC. Sources below support methods, not an unverified geometry identity.

## Hadronic calorimetry

1. CALICE, *Hadronic energy resolution of a highly granular scintillator-steel hadron calorimeter
   using software compensation techniques*: https://arxiv.org/abs/1207.4210
   - Local/global energy-density information improved single-hadron resolution in a granular
     scintillator-steel HCAL. Decision: preserve density and longitudinal shower information.
2. CALICE, *Software Compensation for Highly Granular Calorimeters using Machine Learning*:
   https://arxiv.org/abs/2403.04632
   - Spatial, temporal, and energy information learned depth/leakage-related compensation and improved
     linearity/resolution. Decision: make energy compensation, depth, and containment central.
3. Akchurin et al., *On the Use of Neural Networks for Energy Reconstruction in High-granularity
   Calorimeters*: https://arxiv.org/abs/2107.10207
   - CNN/GNN cell-level models can improve energy reconstruction in fine segmented simulation.
     Decision: test a compact grid network, while preserving simulation-domain limitations.
4. CMS HGCAL/CALICE, *Using graph neural networks to reconstruct charged pion showers in the CMS High
   Granularity Calorimeter*: https://arxiv.org/abs/2406.11937
   - Dynamic graph reconstruction compensates shower multiplicity/spatial fluctuations and leakage on
     test-beam data. Decision: topology is credible, but GNN remains gated for this regular grid.

## Model classes and representation

5. Chen and Guestrin, *XGBoost: A Scalable Tree Boosting System*:
   https://arxiv.org/abs/1603.02754
   - Decision: retain boosted trees as a strong engineered-feature baseline.
6. Grinsztajn et al., *Why do tree-based models still outperform deep learning on tabular data?*:
   https://arxiv.org/abs/2207.08815
   - Decision: a neural model must earn its added cost; it is not presumed superior on scalar inputs.
7. Gorishniy et al., *Revisiting Deep Learning Models for Tabular Data*:
   https://arxiv.org/abs/2106.11959
   - Decision: there is no universally superior tabular learner; compare under one protocol.
8. Zaheer et al., *Deep Sets*: https://arxiv.org/abs/1703.06114
   - Decision: if grid mapping loses information, the first irregular-hit fallback is a small
     permutation-invariant set model.
9. Komiske et al., *Energy Flow Networks: Deep Sets for Particle Jets*:
   https://arxiv.org/abs/1810.05165
   - Decision: set aggregation is a principled particle-physics representation, but this work does not
     claim infrared/collinear safety for calorimeter hits.
10. XGBoost official parameter documentation:
    https://xgboost.readthedocs.io/en/stable/parameter.html
    - Confirms CUDA, Pseudo-Huber, quantile, and multi-output status. Decision: single-output heads and
      bounded official objectives.
11. XGBoost official monotonic-constraint documentation:
    https://xgboost.readthedocs.io/en/stable/tutorials/monotonic.html
    - Warns histogram constraints can yield shallow trees. Decision: constraints are an ablation, not
      an unquestioned prior.

## Splits, calibration, and uncertainty

12. Scikit-learn `StratifiedGroupKFold` official API:
    https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.StratifiedGroupKFold.html
    - Decision: preserve nonoverlapping groups while balancing label strata.
13. Tampu et al., *Inflation of test accuracy due to data leakage in deep learning-based
    classification of OCT images*: https://arxiv.org/abs/2202.12267
    - Demonstrates correlated-sample split inflation. Decision: group and detector-fingerprint gates.
14. Scikit-learn `IsotonicRegression` official API:
    https://scikit-learn.org/stable/modules/generated/sklearn.isotonic.IsotonicRegression.html
    - Decision: one monotone global response mapping after champion freeze.
15. Romano, Patterson, and Candès, *Conformalized Quantile Regression*:
    https://arxiv.org/abs/1905.03222
    - Shows split calibration can produce finite-sample marginal coverage under exchangeability.
      Decision: because this study intentionally reuses validation for selection and calibration, its
      intervals are labeled empirical and coverage is measured on locked test.

## Cloud execution

16. Google Cloud, create a custom/serverless training job:
    https://cloud.google.com/vertex-ai/docs/training/create-custom-job
17. Google Cloud, configure training compute:
    https://cloud.google.com/vertex-ai/docs/training/configure-compute
18. Google Cloud Billing budgets:
    https://cloud.google.com/billing/docs/how-to/budgets
    - Google explicitly states that setting a budget does not automatically cap usage/spending.
      Decision: $78 operational maximum, job timeouts, one replica/concurrent trial, and a manual
      committed-cost ledger under the $90 absolute cap.

## Reproducibility standard used for QC

The target standard is an applied-ML/HEP calorimeter reconstruction package suitable for a rigorous
internal physics performance review: executable data contract, fixed evaluation, baselines,
uncertainty caveats, complete provenance, group-aware statistics, cost accounting, and a clean source
archive. This is stricter and more appropriate than claiming journal acceptance before a real data run
exists.
