"""Delete GitHub Actions workflow runs older than N days.

Uses the `gh` CLI (already authenticated in the workflow) to list and delete
runs, so no extra auth is needed. Supports a dry-run so you can preview first.

Usage:
    python clean_old_runs.py --days 7 --dry-run true
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone


def list_runs():
    """Return the most recent runs as a list of {databaseId, createdAt}."""
    result = subprocess.run(
        ["gh", "run", "list", "--limit", "100", "--json", "databaseId,createdAt"],
        capture_output=True, text=True, check=True,
    )
    return json.loads(result.stdout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Clean old workflow runs.")
    parser.add_argument("--days", type=int, default=7, help="Delete runs older than this many days.")
    parser.add_argument("--dry-run", default="true", help="'true' = preview only, 'false' = delete.")
    args = parser.parse_args()

    cutoff = datetime.now(timezone.utc) - timedelta(days=args.days)
    dry_run = args.dry_run.lower() == "true"

    deleted = 0
    for run in list_runs():
        created = datetime.fromisoformat(run["createdAt"].replace("Z", "+00:00"))
        if created >= cutoff:
            continue
        run_id = run["databaseId"]
        if dry_run:
            print(f"Would delete run {run_id} (created {run['createdAt']})")
        else:
            subprocess.run(["gh", "run", "delete", str(run_id)], check=False)
            print(f"Deleted run {run_id}")
        deleted += 1

    print(f"Processed {deleted} old workflow runs (dry_run={dry_run}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
