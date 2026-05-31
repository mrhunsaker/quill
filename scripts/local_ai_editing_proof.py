from __future__ import annotations

import argparse
import os
import re
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Profile:
    name: str
    n_ctx: int
    n_batch: int
    max_tokens: int
    temperature: float
    top_p: float


PROFILES: dict[str, Profile] = {
    "low-4gb": Profile(
        name="low-4gb",
        n_ctx=1024,
        n_batch=128,
        max_tokens=220,
        temperature=0.2,
        top_p=0.9,
    ),
    "balanced": Profile(
        name="balanced",
        n_ctx=2048,
        n_batch=256,
        max_tokens=260,
        temperature=0.2,
        top_p=0.9,
    ),
    "quality": Profile(
        name="quality",
        n_ctx=4096,
        n_batch=256,
        max_tokens=320,
        temperature=0.15,
        top_p=0.9,
    ),
}


SCENARIOS: tuple[dict[str, str], ...] = (
    {
        "name": "grammar-fix",
        "instruction": "Fix grammar and punctuation. Keep meaning and keep it concise.",
        "input": "quill are focused on accessibility and it help users write documents faster",
        "reference": "Quill is focused on accessibility, and it helps users write documents faster.",
    },
    {
        "name": "style-rewrite",
        "instruction": "Rewrite as clear release notes text. Keep under 2 sentences.",
        "input": "we changed a bunch of stuff around loading and it should be less crashy now",
        "reference": "We improved loading reliability and reduced crashes during startup.",
    },
    {
        "name": "selection-edit",
        "instruction": "Rewrite this paragraph for plain language and remove repetition.",
        "input": "The installer process process can fail if temporary directories are not writable and this can cause failures in the installer process.",
        "reference": "The installer can fail when temporary directories are not writable.",
    },
)


def _thread_count() -> int:
    cores = os.cpu_count() or 4
    return max(1, min(6, cores // 2))


def _estimate_ram_gb(model_path: Path, profile: Profile) -> float:
    model_gb = model_path.stat().st_size / (1024**3)
    # Coarse estimate for CPU inference footprint.
    kv_gb = (profile.n_ctx / 1024.0) * 0.18
    overhead_gb = 0.7
    return model_gb + kv_gb + overhead_gb


def _simple_similarity(a: str, b: str) -> float:
    a_tokens = set(re.findall(r"[a-z0-9']+", a.lower()))
    b_tokens = set(re.findall(r"[a-z0-9']+", b.lower()))
    if not a_tokens or not b_tokens:
        return 0.0
    inter = len(a_tokens & b_tokens)
    union = len(a_tokens | b_tokens)
    return inter / union


def _score_output(candidate: str, reference: str, original: str) -> tuple[float, list[str]]:
    reasons: list[str] = []
    sim = _simple_similarity(candidate, reference)
    changed = candidate.strip().lower() != original.strip().lower()

    if not changed:
        reasons.append("output unchanged")
    if len(candidate.strip()) < 12:
        reasons.append("output too short")

    score = sim
    if changed:
        score += 0.08
    if candidate.strip().endswith((".", "!", "?")):
        score += 0.04
    score = max(0.0, min(1.0, score))

    if score < 0.35:
        reasons.append("low semantic match to reference")

    return score, reasons


def _build_prompt(instruction: str, text: str) -> str:
    return (
        "You are an expert text editor for accessibility-focused writing software. "
        "Return only the edited text, with no commentary.\n\n"
        f"Instruction: {instruction}\n"
        f"Text: {text}\n"
        "Edited text:"
    )


def _word_like_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z0-9']+", text))


def _run_inference(
    llm,
    prompt: str,
    profile: Profile,
    *,
    stream_metrics: bool,
) -> tuple[str, float, float | None, float | None]:
    """Return output, total seconds, first-token seconds, and words/second."""
    start = time.perf_counter()
    if not stream_metrics:
        result = llm(
            prompt,
            max_tokens=profile.max_tokens,
            temperature=profile.temperature,
            top_p=profile.top_p,
            stop=["\n\nInstruction:", "\nText:"],
        )
        elapsed = time.perf_counter() - start
        output = result["choices"][0]["text"].strip()
        return output, elapsed, None, None

    first_token_seconds: float | None = None
    chunks: list[str] = []
    iterator = llm(
        prompt,
        max_tokens=profile.max_tokens,
        temperature=profile.temperature,
        top_p=profile.top_p,
        stop=["\n\nInstruction:", "\nText:"],
        stream=True,
    )
    for piece in iterator:
        text_piece = piece["choices"][0].get("text", "")
        if text_piece and first_token_seconds is None:
            first_token_seconds = time.perf_counter() - start
        chunks.append(text_piece)

    elapsed = time.perf_counter() - start
    output = "".join(chunks).strip()
    words = _word_like_count(output)
    words_per_sec = (words / elapsed) if elapsed > 0 else None
    return output, elapsed, first_token_seconds, words_per_sec


def _load_llm(model_path: Path, profile: Profile):
    try:
        from llama_cpp import Llama
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Could not import llama_cpp: {exc}") from exc

    try:
        return Llama(
            model_path=str(model_path),
            n_ctx=profile.n_ctx,
            n_batch=profile.n_batch,
            n_threads=_thread_count(),
            verbose=False,
        )
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Model load failed: {exc}") from exc


def run_proof(
    model_path: Path,
    profile: Profile,
    max_ram_gb: float | None,
    *,
    stream_metrics: bool,
) -> int:
    if not model_path.exists():
        print(f"FAIL: model file does not exist: {model_path}")
        return 2

    est = _estimate_ram_gb(model_path, profile)
    print(f"Model: {model_path.name}")
    print(f"Profile: {profile.name}")
    print(f"Estimated RAM use: {est:.2f} GB")

    if max_ram_gb is not None and est > max_ram_gb:
        print(
            "FAIL: Estimated RAM exceeds limit "
            f"({est:.2f} GB > {max_ram_gb:.2f} GB)."
        )
        return 3

    try:
        llm = _load_llm(model_path, profile)
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return 4

    total_score = 0.0
    scenario_count = len(SCENARIOS)
    hard_fail = False

    for scenario in SCENARIOS:
        prompt = _build_prompt(scenario["instruction"], scenario["input"])
        try:
            output, elapsed, first_token_seconds, words_per_sec = _run_inference(
                llm,
                prompt,
                profile,
                stream_metrics=stream_metrics,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL: scenario {scenario['name']} crashed: {exc}")
            hard_fail = True
            continue

        score, reasons = _score_output(output, scenario["reference"], scenario["input"])
        total_score += score

        print(f"\n[{scenario['name']}] {elapsed:.2f}s")
        if first_token_seconds is not None:
            print(f"First token: {first_token_seconds:.2f}s")
        if words_per_sec is not None:
            print(f"Throughput: {words_per_sec:.2f} words/s")
        print(f"Output: {output}")
        print(f"Score: {score:.2f}")
        if reasons:
            print("Notes:")
            for reason in reasons:
                print(f"- {reason}")

    avg = total_score / scenario_count if scenario_count else 0.0
    print("\n=== Summary ===")
    print(f"Average quality score: {avg:.2f}")

    if hard_fail:
        print("FAIL: at least one scenario crashed.")
        return 5
    if avg < 0.45:
        print("FAIL: quality below threshold for editing use.")
        return 6

    print("PASS: workable baseline for local editing scenarios.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Standalone local-model proof for QUILL editing quality and low-memory viability."
        )
    )
    parser.add_argument("--model", required=True, help="Path to GGUF model file")
    parser.add_argument(
        "--profile",
        choices=tuple(PROFILES.keys()),
        default="low-4gb",
        help="Runtime profile to emulate target machine class",
    )
    parser.add_argument(
        "--max-ram-gb",
        type=float,
        default=None,
        help="Optional hard memory budget gate (for example 4.0)",
    )
    parser.add_argument(
        "--stream-metrics",
        action="store_true",
        help="Use streaming inference to report first-token latency and throughput.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = PROFILES[args.profile]
    model_path = Path(args.model)
    return run_proof(
        model_path,
        profile,
        args.max_ram_gb,
        stream_metrics=args.stream_metrics,
    )


if __name__ == "__main__":
    raise SystemExit(main())
