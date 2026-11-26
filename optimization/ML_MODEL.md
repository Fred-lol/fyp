# Learned strategy ranking

The default shared generate_plan function calls a trained multi-output ridge regressor. It predicts the relative quality rank of each geometric packing strategy from load and lorry features. Predicted ranks determine search order under the existing time budget; geometric feasibility checks and independent validation determine acceptance. Orientations are still selected by the geometric search, not by a learned placement model.

Training: run `.venv/Scripts/python scripts/train_strategy_model.py` from the repository root. NumPy 2.5.4 is pinned. Seeds 0-79 train the model; seeds 80-99 are held-out scenarios. Labels come from actual independently validated packing results, ranked by the optimizer objective. Synthetic scenarios are small (4-18 boxes) and are not production fleet evidence.

The checked-in JSON artifact contains only coefficients and metadata, never executable pickle data. Missing, incompatible or malformed artifacts fall back to the fixed strategy order. Training does not run at application startup. Historical plans are untouched.

Evaluation is recorded in ml_evaluation.json. On held-out scenarios both modes found 17/20 valid layouts, with equal compactness on all 17. Three scenarios yielded no validated complete layout in either mode. Mean successful-run times were approximately 0.097 seconds each. These results do not demonstrate improved final packing quality; full search often visits all strategies. The learned first-choice mean relative rank was 0.154 versus 0.242 for the fixed first strategy. Larger and production-like workloads need further evaluation.

No optimality or zero-gap guarantee is made. Deployment and live inference must be verified separately; repository push and an HTTP health response do not establish the deployed commit.
