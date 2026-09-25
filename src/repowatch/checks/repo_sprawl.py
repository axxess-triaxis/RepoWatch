"""Repo sprawl detection.

Two real signals, both cheap (metadata only, no clones):
  1. Near-duplicate repo names within the same org (Levenshtein distance
     below a threshold) -- catches "CopperNick" vs "CopperNick-Vision"
     -style forks-of-intent, which are legitimate renames but also exactly
     the shape a genuine accidental duplicate takes, so both get surfaced
     for a human to tell apart.
  2. Raw repo count over a threshold, since sprawl is also just "too many
     active surfaces for one org to actually govern."
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..github_client import gh_json

DEFAULT_COUNT_THRESHOLD = 15
DEFAULT_SIMILARITY_THRESHOLD = 0.75  # 0..1, higher = more similar


def _normalized_levenshtein(a: str, b: str) -> float:
    a, b = a.lower(), b.lower()
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            cost = 0 if ca == cb else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    distance = prev[-1]
    return 1.0 - distance / max(len(a), len(b))


@dataclass
class NearDuplicate:
    repo_a: str
    repo_b: str
    similarity: float


@dataclass
class SprawlResult:
    org: str
    total_active_repos: int
    over_threshold: bool
    near_duplicates: list[NearDuplicate] = field(default_factory=list)
    error: str | None = None


def check(
    org: str,
    count_threshold: int = DEFAULT_COUNT_THRESHOLD,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
) -> SprawlResult:
    try:
        repos = gh_json(
            ["repo", "list", org, "--limit", "200", "--json", "name,isArchived,isFork"]
        )
    except Exception as e:  # noqa: BLE001
        return SprawlResult(org=org, total_active_repos=0, over_threshold=False, error=str(e))

    active = [r["name"] for r in (repos or []) if not r.get("isArchived") and not r.get("isFork")]

    dupes: list[NearDuplicate] = []
    for i, name_a in enumerate(active):
        for name_b in active[i + 1 :]:
            sim = _normalized_levenshtein(name_a, name_b)
            if sim >= similarity_threshold:
                dupes.append(NearDuplicate(repo_a=name_a, repo_b=name_b, similarity=round(sim, 2)))

    return SprawlResult(
        org=org,
        total_active_repos=len(active),
        over_threshold=len(active) > count_threshold,
        near_duplicates=dupes,
    )
