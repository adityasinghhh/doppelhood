"""Report where commonly made neighborhood comparisons rank in the matcher's output.

For each pair in config/validation.yaml, finds the rank of the best accepted
neighborhood among every neighborhood in the target city, then summarizes how
many land first and in the top five, the median rank, and the mean reciprocal
rank.
"""

import argparse
from pathlib import Path

import numpy as np
import yaml

from doppelhood import match

VALIDATION = Path("config/validation.yaml")


def evaluate(hoods, overall, pairs):
    """Each pair's rank (1 is the best match), or None when a neighborhood is missing."""
    index = {n["id"]: i for i, n in enumerate(hoods)}
    results = []
    for pair in pairs:
        i = index.get(pair["from"])
        targets = [j for j, n in enumerate(hoods) if n["city"] == pair["to"]]
        accepted = [index[f"{pair['to']}:{name}"] for name in pair["accept"] if f"{pair['to']}:{name}" in index]
        if i is None or not accepted:
            results.append((pair, None, None))
            continue
        order = sorted(targets, key=lambda j: overall[i, j], reverse=True)
        rank = min(order.index(j) for j in accepted) + 1
        results.append((pair, rank, hoods[order[0]]["name"]))
    return results


def summary(results):
    ranks = [r for _, r, _ in results if r is not None]
    return {
        "pairs": len(ranks),
        "first": sum(r == 1 for r in ranks),
        "top5": sum(r <= 5 for r in ranks),
        "median": float(np.median(ranks)),
        "mrr": round(float(np.mean([1 / r for r in ranks])), 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("cities", nargs="*", help="city slugs to load (default: all)")
    args = parser.parse_args()

    config = yaml.safe_load(Path("config/cities.yaml").read_text())
    cities = [c for c in config["cities"] if not args.cities or c["slug"] in args.cities]
    hoods = [n for city in cities for n in match.load_city(city)]
    overall, _ = match.score(hoods, match.Embedder())

    pairs = yaml.safe_load(VALIDATION.read_text())["pairs"]
    results = evaluate(hoods, overall, pairs)
    for pair, rank, top in results:
        if rank is None:
            print(f"  missing  {pair['from']} -> {pair['to']}")
        else:
            print(f"  {rank:4}  {pair['from']} -> {pair['to']} (top: {top})")
    print(summary(results))


if __name__ == "__main__":
    main()
