"""
Transform all data from raw_data to core tables.
Runs transformers in dependency order: locations → orders → order_items → metadata
"""

from .transform_locations import transform_locations
from .transform_orders import transform_orders
from .transform_order_items import transform_order_items
from .transform_enriched_orders import transform_enriched_orders

# Pipeline steps in dependency order
STEPS = [
    ("locations", transform_locations),
    ("orders", transform_orders),
    ("order_items", transform_order_items),
    ("metadata", transform_enriched_orders),
]


def transform_all() -> dict:
    """Transform all data from raw_data to core tables."""
    print("=" * 50)
    print("TRANSFORMING: RAW → CORE")
    print("=" * 50)
    
    results = {}
    for i, (name, func) in enumerate(STEPS, 1):
        print(f"\n[{i}/{len(STEPS)}] {name}...")
        results[name] = func()
        total = sum(v for k, v in results[name].items() if k != "errors")
        errors = results[name].get("errors", 0)
        print(f"[OK] {total} {name}" + (f" ({errors} errors)" if errors else ""))
    
    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for name, counts in results.items():
        total = sum(v for k, v in counts.items() if k != "errors")
        print(f"  {name}: {total}")
    
    return results


if __name__ == "__main__":
    transform_all()
