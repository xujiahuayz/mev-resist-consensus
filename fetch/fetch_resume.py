"""
Resume-capable block fetcher. Skips blocks already on disk.

Usage:
    python fetch/fetch_resume.py

Fetches ~1001 blocks per period into data/fetch/<PERIOD>/, resuming from where
a previous run left off. Uses the same JSON format as fetch.py.

Note: FTX_COLLAPSE block range is corrected to 15970000-15971000 (Nov 10-11 2022).
The original fetch.py erroneously used 16000000, the same range as STABLE_POST_MERGE_2022.
"""

import json
import os
import sys
import time
from pathlib import Path
from web3 import Web3

INFURA_URL = "https://mainnet.infura.io/v3/dd763ae6e7ca4f059f69f4589ad695f0"
OUTPUT_DIR = Path("data/fetch")

PERIOD_RANGES = {
    "STABLE_PRE_MERGE_2022":   (15000000, 15001000),
    "STABLE_POST_MERGE_2022":  (16000000, 16001000),
    "STABLE_POST_MERGE_2023":  (17500000, 17501000),
    "FTX_COLLAPSE_NOV_2022":   (15970000, 15971000),
    "LUNA_CRASH_MAY_2022":     (14800000, 14801000),
    "USDC_DEPEG_MARCH_2023":   (16900000, 16901000),
}


def connect():
    w3 = Web3(Web3.HTTPProvider(INFURA_URL))
    if not w3.is_connected():
        print("Failed to connect to Ethereum node. Check Infura URL and network.")
        sys.exit(1)
    print(f"Connected. Current block: {w3.eth.block_number}")
    return w3


def fetch_and_analyze(w3, block_number):
    """Fetch one block and return the block data dict, or None on error."""
    try:
        block = w3.eth.get_block(block_number, full_transactions=True)
    except Exception as e:
        print(f"  Error fetching block {block_number}: {e}")
        return None

    gas_fees = []
    confirm_times = []
    transactions_data = []

    for txn in block["transactions"]:
        try:
            receipt = w3.eth.get_transaction_receipt(txn["hash"])
            gas_fee_wei = txn["gasPrice"] * txn["gas"]
            gas_fee_gwei = w3.from_wei(gas_fee_wei, "gwei")
            confirm_time = receipt["blockNumber"] - txn["blockNumber"]
            tx_data = {
                "hash": txn["hash"].hex(),
                "from": txn["from"],
                "to": txn["to"],
                "value_eth": str(w3.from_wei(txn["value"], "ether")),
                "value_wei": txn["value"],
                "gas": txn["gas"],
                "gas_price_gwei": str(w3.from_wei(txn["gasPrice"], "gwei")),
                "gas_price_wei": txn["gasPrice"],
                "gas_fee_gwei": str(gas_fee_gwei),
                "gas_fee_wei": gas_fee_wei,
                "confirm_time": confirm_time,
                "block_number": txn["blockNumber"],
                "transaction_index": txn["transactionIndex"],
                "nonce": txn["nonce"],
                "input": txn["input"].hex(),
                "receipt_status": receipt["status"],
            }
            gas_fees.append(float(gas_fee_gwei))
            confirm_times.append(confirm_time)
            transactions_data.append(tx_data)
        except Exception as e:
            print(f"  Error processing tx in block {block_number}: {e}")
            continue

    n = len(transactions_data)
    return {
        "block_number": block_number,
        "miner": block["miner"],
        "num_transactions": n,
        "avg_gas_fee_gwei": str(sum(gas_fees) / n) if n else "0",
        "avg_confirm_time_blocks": sum(confirm_times) / n if n else 0,
        "block_size_bytes": block["size"],
        "total_gas_fees_gwei": str(sum(gas_fees)),
        "transactions": transactions_data,
        "gas_fees_gwei": gas_fees,
        "timestamp": block["timestamp"],
    }


def fetch_period_resume(w3, period_name, start, end):
    period_dir = OUTPUT_DIR / period_name
    period_dir.mkdir(parents=True, exist_ok=True)

    total = end - start + 1
    skipped = 0
    fetched = 0
    errors = 0

    print(f"\n{'='*60}")
    print(f"Period: {period_name}  blocks {start}–{end}  ({total} total)")

    for block_num in range(start, end + 1):
        out_file = period_dir / f"block_{block_num}.json"
        if out_file.exists():
            skipped += 1
            continue

        block_data = fetch_and_analyze(w3, block_num)
        if block_data is None:
            errors += 1
            time.sleep(0.5)
            continue

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(block_data, f, indent=4, default=str)

        fetched += 1
        done = skipped + fetched + errors
        print(f"  FETCH block {block_num}  ({done}/{total} processed, {fetched} new)")
        time.sleep(0.1)

    print(f"  Done: {skipped} skipped, {fetched} fetched, {errors} errors")
    return fetched


def main():
    w3 = connect()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for period_name, (start, end) in PERIOD_RANGES.items():
        fetch_period_resume(w3, period_name, start, end)

    print(f"\nAll periods complete. Data saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
