import csv
import os
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def calculate_mev_distribution_from_transactions(file_path):
    """Calculate MEV distribution among builders and users from a single transaction CSV file."""
    required_fields = ['mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at']
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        transactions = list(reader)

        # Check if all required fields are present
        missing_fields = [field for field in required_fields if field not in reader.fieldnames]
        if missing_fields:
            print(f"Skipping file {file_path} due to missing fields: {missing_fields}")
            return None  # Return None if fields are missing

        # Dictionary to store MEV data per block
        block_mev_data = defaultdict(lambda: {"total_mev": 0, "builders_mev": 0, "users_mev": 0})

        # Process each transaction in the file
        for tx in transactions:
            try:
                mev_potential = int(tx['mev_potential'].strip())
                block_num = int(tx['included_at'].strip())
                creator_id = tx['creator_id'].strip()
                
                # Only process transactions with MEV potential
                if mev_potential > 0:
                    block_mev_data[block_num]["total_mev"] += mev_potential
                    target_tx_id = tx['target_tx'].strip()

                    # Find transactions that are targeting the MEV transaction
                    targeting_txs = [t for t in transactions if t.get('target_tx') == target_tx_id]
                    
                    if targeting_txs:
                        # Calculate distances and find closest transactions
                        distances = [abs(int(t['position']) - int(tx['position'])) for t in targeting_txs]
                        min_distance = min(distances)
                        closest_txs = [t for t, d in zip(targeting_txs, distances) if d == min_distance]

                        # Distribute MEV potential among the closest attackers
                        share = mev_potential / len(closest_txs)
                        for closest_tx in closest_txs:
                            if 'builder' in closest_tx['creator_id']:
                                block_mev_data[block_num]["builders_mev"] += share
                            else:
                                block_mev_data[block_num]["users_mev"] += share
            except (ValueError, KeyError) as e:
                print(f"Error in processing transaction: {e}")

    return block_mev_data

def process_all_transactions(data_folder):
    """Process all transaction files in a folder and aggregate MEV distribution data."""
    aggregated_data = defaultdict(lambda: {"total_mev": 0, "builders_mev": 0, "users_mev": 0})

    for filename in os.listdir(data_folder):
        if filename.startswith("pbs_transactions"):
            file_path = os.path.join(data_folder, filename)
            file_data = calculate_mev_distribution_from_transactions(file_path)
            
            if file_data:
                for block_num, data in file_data.items():
                    aggregated_data[block_num]["total_mev"] += data["total_mev"]
                    aggregated_data[block_num]["builders_mev"] += data["builders_mev"]
                    aggregated_data[block_num]["users_mev"] += data["users_mev"]

    return aggregated_data

def plot_mev_distribution(aggregated_data, user_attack_counts):
    """Plot MEV distribution for different user attack configurations."""
    builder_mev = [data["builders_mev"] for data in aggregated_data.values()]
    user_mev = [data["users_mev"] for data in aggregated_data.values()]
    total_mev = [data["total_mev"] for data in aggregated_data.values()]

    x_axis = list(aggregated_data.keys())

    plt.figure(figsize=(12, 6))
    plt.stackplot(x_axis, user_mev, builder_mev, labels=["Users MEV", "Builders MEV"], colors=["blue", "red"])
    plt.xlabel("Block Number")
    plt.ylabel("MEV Distribution (Gwei)")
    plt.title(f"MEV Distribution with User Attack Counts: {user_attack_counts}")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    user_attack_counts = [0, 7, 14, 20]  # Modify or iterate as needed

    for user_count in user_attack_counts:
        aggregated_data = process_all_transactions(data_folder)
        plot_mev_distribution(aggregated_data, user_count)
