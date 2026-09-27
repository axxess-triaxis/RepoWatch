"""GitHub access for every check, through one call: `gh_json(args)`.

By default this runs the `gh` CLI, which is already authenticated on the
user's machine -- no separate token plumbing to get wrong. Services with no
`gh` binary (the RepoWatch GitHub App) call `use_token()` once, and the same
`gh`-style argument lists are then served directly from the REST API with
that token, using the standard library only.
"""

from __future__ import annotations

import http.client
import json
import re
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

API_ROOT = "https://api.github.com"


class GhError(RuntimeError):
    pass


_token: str | None = None


def use_token(token: str | None) -> None:
    """Serve gh_json() from the REST API with `token`; None restores the gh CLI."""
    global _token
    _token = token


def gh_json(args: list[str], timeout: int = 30) -> object:
    """Run `gh <args>` (or its REST equivalent) and return the parsed JSON."""
    if _token is not None:
        return _rest_json(args, timeout)
    return _cli_json(args, timeout)


def _cli_json(args: list[str], timeout: int) -> object:
    # encoding/errors explicit: on Windows, subprocess's text=True decodes
    # with the system codepage (cp1252) by default, not UTF-8 -- and GitHub
    # API responses routinely carry real UTF-8 (emoji in descriptions,
    # non-ASCII commit authors, file content pulled during the PII scan).
    # That mismatch crashed a real full-org run with UnicodeDecodeError.
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )
    if result.returncode != 0:
        raise GhError(f"gh {' '.join(args)} failed: {result.stderr.strip()}")
    if not result.stdout.strip():
        return None
    return json.loads(result.stdout)


# --- REST backend -----------------------------------------------------------
# Covers exactly the gh invocations the checks make:
#   api <path> [--paginate] [-X GET] [-f key=value ...]
#   repo list <owner> --limit N --json name,isArchived,isFork
#   pr list --repo <owner/repo> --state open --limit N --json number,title,createdAt,url


def _rest_json(args: list[str], timeout: int) -> object:
    if args[:1] == ["api"]:
        return _rest_api(args[1:], timeout)
    if args[:2] == ["repo", "list"]:
        return _rest_repo_list(args[2], _flag(args, "--limit", 200), timeout)
    if args[:2] == ["pr", "list"]:
        return _rest_pr_list(args, timeout)
    raise GhError(f"gh {' '.join(args)}: not supported by the token backend")


def _flag(args: list[str], name: str, default: int) -> int:
    return int(args[args.index(name) + 1]) if name in args else default


def _rest_api(rest: list[str], timeout: int) -> object:
    path, params, paginate = rest[0], {}, False
    i = 1
    while i < len(rest):
        if rest[i] == "--paginate":
            paginate = True
        elif rest[i] == "-X":
            if rest[i + 1].upper() != "GET":
                raise GhError("the token backend is read-only")
            i += 1
        elif rest[i] == "-f":
            key, _, value = rest[i + 1].partition("=")
            params[key] = value
            i += 1
        i += 1
    if paginate:
        return _get_all(path, params, timeout)
    return _get(path, params, timeout)[0]


def _get(path: str, params: dict, timeout: int) -> tuple[object, str | None]:
    """One GET; returns (parsed JSON, next-page URL or None)."""
    url = path if path.startswith("https://") else f"{API_ROOT}/{path.lstrip('/')}"
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "repowatch",
        },
    )
    try:
        body, link = _read_with_retry(request, timeout)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(detail).get("message", detail)
        except ValueError:
            pass
        # Same shape as gh's error text, so callers that branch on "403" or
        # "disabled for this repository" behave identically on both backends.
        raise GhError(f"GET {path} failed: {detail} (HTTP {e.code})") from None
    except urllib.error.URLError as e:
        raise GhError(f"GET {path} failed: {e.reason}") from None
    except (http.client.IncompleteRead, ConnectionError) as e:
        raise GhError(f"GET {path} failed: {e!r}") from None
    match = re.search(r'<([^>]+)>;\s*rel="next"', link)
    return (json.loads(body) if body.strip() else None), (match.group(1) if match else None)


def _read_with_retry(request: urllib.request.Request, timeout: int, attempts: int = 3):
    """Read one response, retrying a connection that drops mid-body.

    Large responses (a big repo's recursive tree is ~0.5 MB) occasionally
    arrive truncated as http.client.IncompleteRead; gh retries these itself.
    """
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return (
                    response.read().decode("utf-8", errors="replace"),
                    response.headers.get("Link", ""),
                )
        except (http.client.IncompleteRead, ConnectionError):
            if attempt == attempts - 1:
                raise


def _get_all(path: str, params: dict, timeout: int, limit: int | None = None) -> list:
    """Follow Link: rel="next" and merge list pages, like `gh api --paginate`."""
    items: list = []
    data, next_url = _get(path, {"per_page": "100", **params}, timeout)
    while True:
        page = data if isinstance(data, list) else (data or {}).get("repositories", [])
        items.extend(page)
        if not next_url or (limit is not None and len(items) >= limit):
            break
        data, next_url = _get(next_url, {}, timeout)
    return items[:limit] if limit is not None else items


def _rest_repo_list(owner: str, limit: int, timeout: int) -> list[dict]:
    try:
        repos = _get_all(f"orgs/{owner}/repos", {"type": "all", "sort": "pushed"}, timeout, limit)
    except GhError as e:
        if "(HTTP 404)" not in str(e):
            raise
        repos = _get_all(f"users/{owner}/repos", {"sort": "pushed"}, timeout, limit)
    return [
        {"name": r["name"], "isArchived": r.get("archived", False), "isFork": r.get("fork", False)}
        for r in repos
    ]


def _rest_pr_list(args: list[str], timeout: int) -> list[dict]:
    repo = args[args.index("--repo") + 1]
    state = args[args.index("--state") + 1] if "--state" in args else "open"
    prs = _get_all(f"repos/{repo}/pulls", {"state": state}, timeout, _flag(args, "--limit", 30))
    return [
        {"number": p["number"], "title": p["title"], "createdAt": p["created_at"], "url": p["html_url"]}
        for p in prs
    ]


def list_org_repos(org: str) -> list[str]:
    """Real repo names for an org, non-archived, non-fork by default caller's choice."""
    data = gh_json(
        ["repo", "list", org, "--limit", "200", "--json", "name,isArchived"]
    )
    return [r["name"] for r in data if not r.get("isArchived")]


@dataclass(frozen=True)
class RepoRef:
    org: str
    name: str

    @property
    def full_name(self) -> str:
        return f"{self.org}/{self.name}"
