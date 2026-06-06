"""Tiny example script run from a GitHub Actions workflow.

Demonstrates running a Python .py file on disk, reading a CLI argument,
and exiting with a clear status code.
"""

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Print a greeting and the Behave tag.")
    parser.add_argument("--tag", default="smoke", help="Behave tag to report.")
    args = parser.parse_args()

    print(f"Hello from hello.py running on Python {sys.version.split()[0]}")
    print(f"Selected Behave tag: {args.tag}")
    print(f"Example command: behave --tags={args.tag} --no-capture")
    return 0


if __name__ == "__main__":
    sys.exit(main())
