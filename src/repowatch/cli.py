"""RepoWatch CLI entry point."""

from __future__ import annotations

import argparse
from pathlib import Path

from .report import run_audit, write_html, write_json


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="repowatch",
        description="Audit an org's repos for the failure modes AI-assisted teams actually hit.",
    )
    parser.add_argument("org", help="GitHub org or user to audit, e.g. axxess-triaxis")
    parser.add_argument(
        "--repos", nargs="*", default=None,
        help="Specific repo names to audit (default: every active, non-fork repo in the org)",
    )
    parser.add_argument("--out", default="repowatch_report", help="Output file prefix")
    args = parser.parse_args()

    print(f"Auditing {args.org} ...")
    report = run_audit(args.org, args.repos)

    json_path = Path(f"{args.out}.json")
    html_path = Path(f"{args.out}.html")
    write_json(report, json_path)
    write_html(report, html_path)

    print(f"Scanned {report['repos_scanned']} repos.")
    print(f"JSON: {json_path}")
    print(f"HTML: {html_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
