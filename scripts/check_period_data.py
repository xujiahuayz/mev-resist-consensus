"""
Check why period simulations show no difference: verify fetch data and period mapping.

Reports:
- Block numbers in data/fetch (flat or per subdir)
- Which period each block range maps to (period_definitions)
- Whether the loader finds any period-specific data

Run: python scripts/check_period_data.py
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FETCH_BASE = PROJECT_ROOT / "data" / "fetch"
sys.path.insert(0, str(PROJECT_ROOT))


def main():
    from blockchain_env.period_definitions import BLOCK_RANGES_BY_PERIOD, period_for_block

    print("=" * 60)
    print("Period data check (why no difference between periods?)")
    print("=" * 60)

    print("\n1. Period definitions (block ranges):")
    for name, (start, end) in BLOCK_RANGES_BY_PERIOD.items():
        print(f"   {name}: {start:,} – {end:,}")

    if not FETCH_BASE.exists():
        print("\n2. data/fetch: directory does not exist. Run fetch/fetch.py first.")
        return

    # Flat files
    flat_files = list(FETCH_BASE.glob("block_*.json"))
    period_dirs = [d for d in FETCH_BASE.iterdir() if d.is_dir() and not d.name.startswith(".")]

    print("\n2. Contents of data/fetch:")
    print(f"   Flat block_*.json files: {len(flat_files)}")
    print(f"   Period subdirs: {[d.name for d in period_dirs]}")

    if flat_files:
        block_nums = []
        for f in flat_files[:5]:
            try:
                with open(f, "r") as fp:
                    b = json.load(fp)
                block_nums.append(b.get("block_number", f.stem.replace("block_", "")))
            except Exception:
                block_nums.append(f.stem.replace("block_", ""))
        if len(flat_files) > 5:
            block_nums.append("...")
            for f in flat_files[-2:]:
                try:
                    with open(f, "r") as fp:
                        b = json.load(fp)
                    block_nums.append(b.get("block_number", f.stem.replace("block_", "")))
                except Exception:
                    block_nums.append(f.stem.replace("block_", ""))
        print(f"   Sample block numbers (flat): {block_nums}")

        # Map first block to period
        try:
            with open(flat_files[0], "r") as fp:
                b = json.load(fp)
            bn = int(b.get("block_number", flat_files[0].stem.replace("block_", "")))
            period = period_for_block(bn)
            print(f"   period_for_block({bn}) = {repr(period)}")
            if period is None:
                print("   → These block numbers are OUTSIDE all period ranges above.")
                print("   → Loader will assign no blocks to any period → fallback for every period.")
        except Exception as e:
            print(f"   Error reading first file: {e}")

    if period_dirs:
        print("\n3. Blocks per period subdir:")
        for d in sorted(period_dirs):
            files = list(d.glob("block_*.json"))
            print(f"   {d.name}: {len(files)} block files")
        print("   If these counts are > 0, the loader will use period-specific data.")
    else:
        print("\n3. No period subdirs. Loader will only use flat block_*.json and partition by block number.")
        print("   If flat blocks are outside the ranges in (1), no period gets data.")

    # Loader
    print("\n4. EthereumDataLoader result:")
    try:
        from blockchain_env.data_loader import EthereumDataLoader
        loader = EthereumDataLoader()
        names = loader.get_period_names()
        if names:
            for n in names:
                d = loader.periods_data[n]
                print(f"   Loaded {n}: {len(d['gas_fees'])} gas fees, {len(d['transactions'])} transactions")
        else:
            print("   No periods loaded → run_experiments_by_period uses FALLBACK for every period.")
            print("   Fix: run fetch/fetch.py so data/fetch has period subdirs with blocks in the ranges in (1).")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("See docs/PERIOD_DATA_MISMATCH.md for full explanation and fix.")
    print("=" * 60)


if __name__ == "__main__":
    main()
