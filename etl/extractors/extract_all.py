"""
Extracts all source data and loads into raw_data table.
Uses hash map for O(1) result aggregation across sources.
"""

import sys
from pathlib import Path
from .extract_doordash import extract_doordash
from .extract_square import extract_square
from .extract_toast import extract_toast

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Source configurations: (name, path_resolver, extractor)
SOURCES = [
    ("doordash", lambda d: d / "doordash_orders.json", extract_doordash),
    ("square", lambda d: d / "square", extract_square),
    ("toast", lambda d: d / "toast_pos_export.json", extract_toast),
]


def extract_all(sources_dir: Path) -> dict:
    """Extracts all source data. Returns dict with counts per source."""
    print("=" * 60 + "\nEXTRACTING ALL SOURCE DATA\n" + "=" * 60)
    
    results = {}
    for i, (name, get_path, extractor) in enumerate(SOURCES, 1):
        path = get_path(sources_dir)
        print(f"\n[{i}/{len(SOURCES)}] {name.title()}...")
        
        if path.exists():
            results[name] = extractor(path)
        else:
            print(f"  [WARNING] Not found: {path}")
            results[name] = {}
    
    # Summary using dict comprehension for aggregation
    print("\n" + "=" * 60 + "\nEXTRACTION SUMMARY\n" + "=" * 60)
    
    metrics = ["locations", "orders", "payments"]
    totals = {m: sum(r.get(m, 0) for r in results.values()) for m in metrics}
    
    for name, counts in results.items():
        stats = " | ".join(f"{m}: {counts.get(m, 0)}" for m in metrics if m in counts)
        print(f"  {name.upper()}: {stats}")
    
    print(f"\n  TOTAL: " + " | ".join(f"{m}: {v}" for m, v in totals.items() if v))
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    sources_dir = Path(__file__).parent.parent.parent / "etl" / "data" / "sources"
    extract_all(sources_dir)
