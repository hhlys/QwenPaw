"""Export project runtime dependencies from pyproject.toml.

This keeps Docker's third-party dependency layer independent from the
frequently changing project wheel layer.
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pyproject", default="pyproject.toml")
    parser.add_argument("--out", default="build/runtime-requirements.txt")
    args = parser.parse_args()

    pyproject_path = Path(args.pyproject)
    output_path = Path(args.out)

    data = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
    dependencies = data.get("project", {}).get("dependencies", [])
    if not dependencies:
        raise SystemExit("No [project].dependencies found")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(str(dep) for dep in dependencies) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(dependencies)} dependencies to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
