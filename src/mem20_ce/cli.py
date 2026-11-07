"""Minimal CLI for mem20-ce."""

import argparse
import json
from .engine import MemoryEngine


def main() -> None:
    parser = argparse.ArgumentParser(prog="mem20-ce", description="mem20 Core Edition")
    parser.add_argument("--store", default="~/.mem20-ce/store", help="Store path")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_rem = sub.add_parser("remember", help="Store a grounded fact")
    p_rem.add_argument("content")
    p_rem.add_argument("--tag", action="append", default=[])

    p_sim = sub.add_parser("simulate", help="Store a simulated hypothesis")
    p_sim.add_argument("content")

    p_rec = sub.add_parser("recall", help="Recall grounded memory")
    p_rec.add_argument("query")
    p_rec.add_argument("-k", type=int, default=5)

    sub.add_parser("health", help="Store health + contamination")
    sub.add_parser("contamination", help="Contamination report")

    args = parser.parse_args()
    eng = MemoryEngine(store_path=args.store)

    if args.cmd == "remember":
        rid = eng.remember(args.content, tags=args.tag)
        print(rid)
    elif args.cmd == "simulate":
        rid = eng.remember_simulated(args.content)
        print(rid)
    elif args.cmd == "recall":
        res = eng.recall(args.query, k=args.k)
        print(json.dumps({"hits": res.hits, "healthy": res.healthy}, indent=2))
    elif args.cmd == "health":
        print(json.dumps(eng.health(), indent=2))
    elif args.cmd == "contamination":
        c = eng.contamination()
        print(json.dumps({
            "contamination_rate": c.contamination_rate,
            "grounded_count": c.grounded_count,
            "simulated_count": c.simulated_count,
            "violations": c.violations,
            "healthy": c.healthy,
        }, indent=2))


if __name__ == "__main__":
    main()
