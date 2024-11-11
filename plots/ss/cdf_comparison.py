import csv
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def calculate_mev_distribution_for_cdf(file_path):
    """Calculate MEV distribution between builders and validators for a single transaction CSV file."""
    required_fields = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        
        if not required_fields.issubset(reader.fieldnames):
            print(f"Skipping file {file_path} due to missing fields.")
            return None

        mev_data = {"total_mev": 0, "validators_mev": [], "builders_mev": []}
        
        transactions = list(reader)
        
        for tx in transactions:
            try:
                mev_potential = int(tx['mev_potential'].strip())
                creator_id = tx['creator_id'].strip()
                
                if mev_potential > 0:
                    mev_data["total_mev"] += mev_potential
                    targeting_txs = [
                        t for t in transactions if t.get('target_tx') == tx['id']
                    ]
                    
                    if targeting_txs:
                        min_distance = min(abs(int(t['position']) - int(tx['position'])) for t in targeting_txs)
                        closest_txs = [t for t in targeting_txs if abs(int(t['position']) - int(tx['position'])) == min_distance]

                        share = mev_potential / len(closest_txs)
                        for closest_tx in closest_txs:
                            if 'builder' in closest_tx['creator_id']:
                                mev_data["builders_mev"].append(share)
                            elif 'validator' in closest_tx['creator_id']:
                                mev_data["validators_mev"].append(share)
            except (ValueError, KeyError) as e:
                print(f"Error in processing transaction: {e}")

    return mev_data

def process_all_transactions_for_cdf(data_folder, builder_attack_count, user_attack_count):
    """Aggregate MEV distribution for builders and validators from all transaction files matching the specified builder and user attack counts."""
    total_validators_mev = []
    total_builders_mev = []

    for filename in os.listdir(data_folder):
        if filename.startswith("pbs_transactions") and f"builders{builder_attack_count}" in filename and f"users{user_attack_count}" in filename:
            file_path = os.path.join(data_folder, filename)
            file_data = calculate_mev_distribution_for_cdf(file_path)
            
            if file_data:
                total_validators_mev.extend(file_data["validators_mev"])
                total_builders_mev.extend(file_data["builders_mev"])

    return total_validators_mev, total_builders_mev

def calculate_cdf(data):
    """Calculate the CDF for a given data list."""
    sorted_data = np.sort(data)
    cdf = np.arange(1, len(sorted_data) + 1) / len(sorted_data)
    return sorted_data, cdf

def plot_mev_cdf(data_folder, output_folder, user_attack_count):
    """Plot the CDFs for MEV profit distribution between validators and builders under different conditions."""
    os.makedirs(output_folder, exist_ok=True)
    plt.figure(figsize=(10, 8))

    # Define different attack configurations to plot
    builder_counts = [0, 10, 20]
    
    for builder_attack_count in builder_counts:
        validators_mev, builders_mev = process_all_transactions_for_cdf(data_folder, builder_attack_count, user_attack_count)
        
        # Calculate CDFs
        validators_mev_sorted, validators_cdf = calculate_cdf(validators_mev)
        builders_mev_sorted, builders_cdf = calculate_cdf(builders_mev)
        
        # Plot CDFs
        plt.plot(builders_mev_sorted, builders_cdf, label=f'PBS - Builders {builder_attack_count} Attackers', linestyle='--')
        plt.plot(validators_mev_sorted, validators_cdf, label=f'PoS - Validators {builder_attack_count} Attackers', linestyle='-')

    plt.xlabel("MEV Profit (Gwei)", fontsize=16)
    plt.ylabel("Cumulative Distribution Function (CDF)", fontsize=16)
    plt.legend(loc="lower right", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.margins(x=0, y=0)
    plt.tight_layout()
    
    # Save and display plot
    output_path = os.path.join(output_folder, "mev_profit_distribution_cdf.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"CDF plot saved to {output_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    output_folder = 'figures/ss'
    user_attack_count = 25  # Fixed 25 user attackers as specified

    plot_mev_cdf(data_folder, output_folder, user_attack_count)
