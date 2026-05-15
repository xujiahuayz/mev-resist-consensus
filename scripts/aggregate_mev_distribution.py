"""Aggregate MEV distribution data across PoS/PBS simulation CSVs with corrected victim utility model.

Corrected model (Task 1):
  When transaction x_j is sandwiched, the attacker captures m_j = mev_potential.
  The victim retains  u_j = v_j * (1 - impact_fraction) - g_j,
  where impact_fraction = m_j / v_j  (capped at 1) and v_j = VALUATION_FACTOR * m_j.

  In the plot denominator we use sum(v_j) instead of sum(m_j), so the percentages
  correctly show what fraction of the *total value at stake* each party captures.
  The "uncaptured" slice now includes victim residual value.

VALUATION_FACTOR = 2  → victim retains half her valuation after the attack.
"""

import csv
import json
import os
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Victim's transaction valuation = VALUATION_FACTOR * mev_potential
# Attacker extracts mev_potential; victim retains (VALUATION_FACTOR-1)*mev_potential - gas_fee
VALUATION_FACTOR = 2.0

# ─── helpers ────────────────────────────────────────────────────────────────

def _is_validator(creator_id: str) -> bool:
    return "validator" in creator_id.lower()

def _is_builder(creator_id: str) -> bool:
    return "builder" in creator_id.lower()


def calculate_mev_distribution(file_path: str, system_type: str) -> dict:
    """Return {'total_mev', '<validators|builders>_mev', 'users_mev'} for one CSV.

    Uses corrected victim utility: total_mev denominator = sum(v_j) = VALUATION_FACTOR * sum(m_j).
    Attacker shares (validators_mev / builders_mev / users_mev) still equal sum(m_j) for their victims.
    """
    required = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}

    attacker_key = "validators_mev" if system_type == "pos" else "builders_mev"
    result = {"total_mev": 0.0, attacker_key: 0.0, "users_mev": 0.0}

    with open(file_path, encoding='utf-8') as f:
        reader = csv.DictReader(f)
        if not required.issubset(set(reader.fieldnames or [])):
            print(f"  Skipping {os.path.basename(file_path)}: missing fields")
            return result
        transactions = list(reader)

    # Index: tx_id → tx row
    tx_by_id = {row['id']: row for row in transactions}

    # Index: victim_tx_id → list of attack tx rows
    attackers_of: dict = defaultdict(list)
    for row in transactions:
        target = row.get('target_tx', '').strip()
        if target and target not in ('', 'None'):
            attackers_of[target].append(row)

    for victim_id, victim in tx_by_id.items():
        try:
            m_j = int(victim['mev_potential'].strip())
        except (ValueError, KeyError):
            continue
        if m_j <= 0:
            continue

        # Victim valuation (corrected model)
        v_j = VALUATION_FACTOR * m_j
        result["total_mev"] += v_j

        attack_txs = attackers_of.get(victim_id, [])
        if not attack_txs:
            # Not sandwiched — MEV remains "uncaptured"
            continue

        # Find the closest attack tx by position distance to victim
        try:
            victim_pos = int(victim['position'])
        except (ValueError, KeyError):
            victim_pos = 0

        valid_attacks = []
        for atx in attack_txs:
            try:
                valid_attacks.append((abs(int(atx['position']) - victim_pos), atx))
            except (ValueError, KeyError):
                pass

        if not valid_attacks:
            continue

        min_dist = min(d for d, _ in valid_attacks)
        closest = [atx for d, atx in valid_attacks if d == min_dist]

        # Share mev_potential equally among closest attackers
        share = m_j / len(closest)
        for atx in closest:
            cid = atx['creator_id'].strip()
            if _is_validator(cid) or _is_builder(cid):
                result[attacker_key] += share
            else:
                result["users_mev"] += share

    return result


def process_pos(data_folder: Path, output_folder: Path) -> None:
    """Aggregate PoS transaction CSVs and write pos_data_user_attack_*.json."""
    user_attack_counts = [0, 12, 24, 50]
    for user_count in user_attack_counts:
        aggregated: dict = {}
        pattern = f"_users{user_count}.csv"
        for fname in sorted(os.listdir(data_folder)):
            if not (fname.startswith("pos_transactions") and fname.endswith(pattern)):
                continue
            try:
                val_count = int(fname.split("validators")[1].split("_")[0])
            except (IndexError, ValueError):
                continue
            file_path = data_folder / fname
            data = calculate_mev_distribution(str(file_path), "pos")
            key = str(val_count)
            if key not in aggregated:
                aggregated[key] = {"total_mev": 0.0, "validators_mev": 0.0, "users_mev": 0.0}
            for k, v in data.items():
                aggregated[key][k] = aggregated[key].get(k, 0.0) + v

        out = output_folder / f"pos_data_user_attack_{user_count}.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2)
        print(f"  Wrote {out.name}  ({len(aggregated)} validator configs)")


def process_pbs(data_folder: Path, output_folder: Path) -> None:
    """Aggregate PBS transaction CSVs and write pbs_data_user_attack_*.json."""
    user_attack_counts = [0, 12, 24, 50]
    for user_count in user_attack_counts:
        aggregated: dict = {}
        pattern = f"_users{user_count}.csv"
        for fname in sorted(os.listdir(data_folder)):
            if not (fname.startswith("pbs_transactions") and fname.endswith(pattern)):
                continue
            try:
                bld_count = int(fname.split("builders")[1].split("_")[0])
            except (IndexError, ValueError):
                continue
            file_path = data_folder / fname
            data = calculate_mev_distribution(str(file_path), "pbs")
            key = str(bld_count)
            if key not in aggregated:
                aggregated[key] = {"total_mev": 0.0, "builders_mev": 0.0, "users_mev": 0.0}
            for k, v in data.items():
                aggregated[key][k] = aggregated[key].get(k, 0.0) + v

        out = output_folder / f"pbs_data_user_attack_{user_count}.json"
        with open(out, 'w', encoding='utf-8') as f:
            json.dump(aggregated, f, indent=2)
        print(f"  Wrote {out.name}  ({len(aggregated)} builder configs)")


if __name__ == "__main__":
    pos_data = PROJECT_ROOT / "data" / "same_seed" / "pos_visible80"
    pbs_data = PROJECT_ROOT / "data" / "same_seed" / "pbs_visible80"
    output = PROJECT_ROOT / "figures" / "ss"
    output.mkdir(parents=True, exist_ok=True)

    print("=== Aggregating PoS data (corrected victim utility) ===")
    process_pos(pos_data, output)

    print("\n=== Aggregating PBS/ePBS data (corrected victim utility) ===")
    process_pbs(pbs_data, output)

    print("\nDone. Run plots/ss/grouped_plots.py to regenerate the MEV distribution plot.")
