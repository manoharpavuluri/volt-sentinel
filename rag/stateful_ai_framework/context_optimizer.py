"""Optional Headroom context optimizer for VoltSentinel RAG.

The optimizer is intentionally optional. If Headroom is not installed or disabled,
it returns the original messages unchanged. Raw evidence and Gold facts should remain
stored outside this function and must be used for deterministic guardrails.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple


@dataclass
class ContextOptimizationResult:
    messages: List[Dict[str, Any]]
    metrics: Dict[str, Any]


def _rough_token_estimate(messages: List[Dict[str, Any]]) -> int:
    text = "\n".join(str(m.get("content", "")) for m in messages)
    return max(1, len(text) // 4)


def optimize_messages_for_llm(
    messages: List[Dict[str, Any]],
    model_name: str,
) -> ContextOptimizationResult:
    """Compress LLM prompt context only when Headroom is enabled.

    Returns original messages when disabled, unavailable, or below threshold.
    """
    enabled = os.getenv("HEADROOM_ENABLED", "false").lower() == "true"
    min_tokens = int(os.getenv("HEADROOM_MIN_INPUT_TOKENS", "4000"))
    tokens_before = _rough_token_estimate(messages)

    if not enabled or tokens_before < min_tokens:
        return ContextOptimizationResult(
            messages=messages,
            metrics={
                "headroom_enabled": False,
                "reason": "disabled_or_below_threshold",
                "tokens_before_estimate": tokens_before,
                "tokens_after_estimate": tokens_before,
                "tokens_saved_estimate": 0,
                "model_name": model_name,
            },
        )

    try:
        # Headroom API may evolve; keep integration isolated here.
        from headroom import compress  # type: ignore

        compressed = compress(messages, model=model_name)
        compressed_messages = getattr(compressed, "messages", messages)
        tokens_after = _rough_token_estimate(compressed_messages)
        return ContextOptimizationResult(
            messages=compressed_messages,
            metrics={
                "headroom_enabled": True,
                "tokens_before_estimate": tokens_before,
                "tokens_after_estimate": tokens_after,
                "tokens_saved_estimate": max(tokens_before - tokens_after, 0),
                "model_name": model_name,
            },
        )
    except Exception as exc:
        return ContextOptimizationResult(
            messages=messages,
            metrics={
                "headroom_enabled": False,
                "reason": f"headroom_unavailable_or_failed: {exc}",
                "tokens_before_estimate": tokens_before,
                "tokens_after_estimate": tokens_before,
                "tokens_saved_estimate": 0,
                "model_name": model_name,
            },
        )
