# AI Distribution Recommendations

## Goal

Define a practical local model distribution plan for QUILL that:

- Works on lower-footprint Windows machines (about 4 GB RAM).
- Delivers higher editing quality on capable machines.
- Does not require Ollama.
- Uses local GGUF + llama-cpp-python directly.

## Proven Baseline

We validated the local runtime stack with a native call test and editing proof harness.

- Runtime install/build status: `llama-cpp-python==0.3.23` installed successfully from source.
- Native runtime check: `from llama_cpp import llama_cpp; llama_cpp.llama_max_devices()` succeeded.
- Existing local model used for proof: `Llama-3.2-1B-Instruct-Q4_K_M.gguf`.
- Proof harness script: `scripts/local_ai_editing_proof.py`.

## Test Results

The following table summarizes measured proof runs against the existing model.

| Profile | RAM Gate | Estimated RAM | Avg Score | Outcome | Notes |
|---|---:|---:|---:|---|---|
| low-4gb | 4.0 GB | 1.63 GB | 0.63 | PASS | Good grammar/cleanup, weaker rewrite quality |
| balanced | 4.0 GB | 1.81 GB | 0.63 | PASS | Similar quality to low-4gb |
| quality | 4.0 GB | 2.17 GB | 0.62 | PASS | No meaningful gain from profile tuning alone |

Interpretation:

- The stack is now stable and usable on lower memory targets.
- Quality ceiling appears model-bound, not profile-bound.
- For stronger editing quality, distribution needs a stronger model tier.

## Distribution Plan

## Tier 1: Low Footprint Default

- Model: 1B to 1.7B instruct GGUF, Q4_K_M.
- Target machines: about 4 GB RAM.
- Typical use: grammar fixes, light rewrites, short drafting.
- Installer behavior: include one small default model or first-run download.

## Tier 2: Quality Upgrade

- Model: around 3B instruct GGUF, Q4_K_M (or Q5_K_M if memory allows).
- Target machines: 6 GB to 8 GB RAM and up.
- Typical use: stronger rewriting, structure edits, tone/style transforms.
- Delivery: optional in-app download from model catalog.

## Tier 3: Optional High Quality

- Model: around 7B instruct GGUF, Q4_K_M.
- Target machines: 12 GB RAM and up.
- Typical use: best local editing quality without cloud.
- Delivery: explicit opt-in download only.

## Candidate Model Shortlist

The following table lists practical candidates for local distribution.

| Tier | Candidate | Size Class | License Family | Notes |
|---|---|---|---|---|
| Low | Llama 3.2 1B Instruct Q4_K_M | ~1B | Llama license | Proven in current environment |
| Low | Qwen2.5 1.5B Instruct Q4_K_M | ~1.5B | Apache 2.0 | Strong low-tier edit quality candidate |
| Quality | Qwen2.5 3B Instruct Q4_K_M | ~3B | Apache 2.0 | Recommended quality tier default |
| High (optional) | 7B instruct Q4_K_M | ~7B | Varies | Best local quality, higher RAM cost |

## Release Recommendation

1. Ship Tier 1 by default for broad compatibility.
2. Offer Tier 2 as the recommended upgrade in first-run AI setup.
3. Keep Tier 3 optional for power users.
4. Use `scripts/local_ai_editing_proof.py` as a release gate for each model tier.

## Suggested Acceptance Gates

- 4 GB gate: model/profile must pass with `--max-ram-gb 4.0`.
- Editing quality gate: average proof score at or above `0.60` for low tier and at or above `0.70` for quality tier.
- Stability gate: zero crashes across all proof scenarios.

## Commands

Run low-footprint proof:

```powershell
python scripts/local_ai_editing_proof.py --model "C:\path\to\model.gguf" --profile low-4gb --max-ram-gb 4.0
```

Run quality-tier proof:

```powershell
python scripts/local_ai_editing_proof.py --model "C:\path\to\model.gguf" --profile quality --max-ram-gb 6.0
```
