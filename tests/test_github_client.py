"""Tests for the token (REST) backend of github_client.gh_json."""

from __future__ import annotations

import io
import json
import urllib.error
from unittest.mock import patch

import pytest

from repowatch import github_client
from repowatch.checks import dependabot


class FakeResponse:
    def __init__(self, body, link: str = ""):
        self._body = json.dumps(body).encode()
        self.headers = {"Link": link}

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


@pytest.fixture(autouse=True)
def token_backend():
    github_client.use_token("test-token")
    yield
    github_client.use_token(None)


def test_api_get_sends_token_and_query_params():
    seen = []

    def fake_urlopen(request, timeout):
        seen.append(request)
        return FakeResponse([{"sha": "abc"}])

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        data = github_client.gh_json(
            ["api", "repos/o/r/commits", "-X", "GET", "-f", "per_page=20"]
        )

    assert data == [{"sha": "abc"}]
    assert seen[0].full_url == "https://api.github.com/repos/o/r/commits?per_page=20"
    assert seen[0].get_header("Authorization") == "Bearer test-token"


def test_paginate_follows_link_header():
    pages = [
        FakeResponse([1, 2], link='<https://api.github.com/next?page=2>; rel="next"'),
        FakeResponse([3]),
    ]
    with patch("urllib.request.urlopen", side_effect=pages):
        data = github_client.gh_json(["api", "repos/o/r/dependabot/alerts", "--paginate"])
    assert data == [1, 2, 3]


def test_non_get_method_is_refused():
    with pytest.raises(github_client.GhError, match="read-only"):
        github_client.gh_json(["api", "repos/o/r/issues", "-X", "POST"])


def test_repo_list_maps_fields_and_falls_back_to_user_repos():
    not_found = urllib.error.HTTPError(
        "u", 404, "Not Found", {}, io.BytesIO(b'{"message": "Not Found"}')
    )
    responses = [not_found, FakeResponse([{"name": "a", "archived": True, "fork": False}])]
    with patch("urllib.request.urlopen", side_effect=responses):
        data = github_client.gh_json(
            ["repo", "list", "someone", "--limit", "200", "--json", "name,isArchived,isFork"]
        )
    assert data == [{"name": "a", "isArchived": True, "isFork": False}]


def test_pr_list_maps_fields():
    pr = {"number": 7, "title": "t", "created_at": "2026-09-01T00:00:00Z", "html_url": "u"}
    with patch("urllib.request.urlopen", return_value=FakeResponse([pr])):
        data = github_client.gh_json(
            ["pr", "list", "--repo", "o/r", "--state", "open", "--limit", "200",
             "--json", "number,title,createdAt,url"]
        )
    assert data == [{"number": 7, "title": "t", "createdAt": "2026-09-01T00:00:00Z", "url": "u"}]


def test_dependabot_disabled_is_detected_through_the_rest_backend():
    forbidden = urllib.error.HTTPError(
        "u", 403, "Forbidden", {},
        io.BytesIO(b'{"message": "Dependabot alerts are disabled for this repository."}'),
    )
    with patch("urllib.request.urlopen", side_effect=forbidden):
        result = dependabot.check("o", "r")
    assert result.dependabot_disabled is True
    assert result.access_denied is False


def test_plain_403_is_access_denied_through_the_rest_backend():
    forbidden = urllib.error.HTTPError(
        "u", 403, "Forbidden", {},
        io.BytesIO(b'{"message": "Resource not accessible by integration"}'),
    )
    with patch("urllib.request.urlopen", side_effect=forbidden):
        result = dependabot.check("o", "r")
    assert result.access_denied is True


def test_truncated_response_is_retried():
    import http.client

    responses = [http.client.IncompleteRead(b"partial", 10), FakeResponse({"ok": True})]
    with patch("urllib.request.urlopen", side_effect=responses):
        assert github_client.gh_json(["api", "repos/o/r"]) == {"ok": True}
