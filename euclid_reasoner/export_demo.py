from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo_prop9 import solve_prop9
from .exporters import hpg_to_graph_json, hpg_to_opml, result_to_hpg


def main() -> None:
    parser = argparse.ArgumentParser(description="Export HPG data from the Prop 9 demo.")
    parser.add_argument("--format", choices=["opml", "graph"], required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    result = solve_prop9()
    hpg = result_to_hpg(result)

    output_path = Path(args.out)
    if args.format == "opml":
        output_path.write_text(hpg_to_opml(hpg), encoding="utf-8")
    else:
        output = hpg_to_graph_json(hpg)
        output_path.write_text(json.dumps(output, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
