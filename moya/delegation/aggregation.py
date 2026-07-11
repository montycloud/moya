"""Named result-aggregation strategies for parallel delegation."""
from __future__ import annotations

from collections import Counter
from typing import Callable, List, Optional

STRATEGIES = frozenset({"concat", "first", "vote", "custom"})


def aggregate(
    results: List[str],
    strategy: str = "concat",
    custom_fn: Optional[Callable[[List[str]], str]] = None,
) -> str:
    """
    Combine a list of agent responses into a single string.

    Strategies:

    * ``"concat"``  — join with a blank line between each result (default).
    * ``"first"``   — return the first result, ignoring the rest.
    * ``"vote"``    — majority vote by exact string match; tie is broken by
                      the most-common result (Counter.most_common order).
    * ``"custom"``  — call *custom_fn(results)* and return its return value.
                      Raises ``ValueError`` if *custom_fn* is not provided.

    Raises:
        ValueError: for an unknown strategy or missing *custom_fn*.
    """
    if strategy == "concat":
        return "\n\n".join(results)

    if strategy == "first":
        return results[0] if results else ""

    if strategy == "vote":
        if not results:
            return ""
        return Counter(results).most_common(1)[0][0]

    if strategy == "custom":
        if custom_fn is None:
            raise ValueError(
                "custom_fn is required when strategy='custom'."
            )
        return custom_fn(results)

    raise ValueError(
        f"Unknown aggregation strategy: {strategy!r}. "
        f"Choose from: {sorted(STRATEGIES)}"
    )
