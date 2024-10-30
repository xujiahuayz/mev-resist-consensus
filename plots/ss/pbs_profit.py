import csv
import os
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def calculate_mev_distribution_from_transactions(file_path):
    """Calculate MEV distribution among builders and users from a single transaction CSV file."""
    required_fields = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames)
        
        # Check if all required fields are present
        if not required_fields.issubset(fieldnames):
            print(f"Skipping file {file_path} due to missing fields.")
            return None  # Skip files with missing fields

        # Dictionary to store MEV data per file configuration
        mev_data = {"total_mev": 0, "builders_mev": 0, "users_mev": 0}
        
        # Collect all transactions
        transactions = list(reader)
        
        # Process each transaction
        for tx in transactions:
            try:
                mev_potential = int(tx['mev_potential'].strip())
                creator_id = tx['creator_id'].strip()
                target_tx_id = tx['target_tx'].strip()
                
                # Only consider transactions with MEV potential
                if mev_potential > 0:
                    mev_data["total_mev"] += mev_potential
                    
                    # Find targeting transactions
                    targeting_txs = [
                        t for t in transactions if t.get('target_tx') == tx['id']
                    ]
                    
                    if targeting_txs:
                        # Find the closest transaction(s) targeting this MEV
                        min_distance = min(abs(int(t['position']) - int(tx['position'])) for t in targeting_txs)
                        closest_txs = [t for t in targeting_txs if abs(int(t['position']) - int(tx['position'])) == min_distance]

                        # Distribute MEV potential among closest attackers
                        share = mev_potential / len(closest_txs)
                        for closest_tx in closest_txs:
                            if 'builder' in closest_tx['creator_id']:
                                mev_data["builders_mev"] += share
                            else:
                                mev_data["users_mev"] += share
            except (ValueError, KeyError) as e:
                print(f"Error in processing transaction: {e}")

    return mev_data

def process_all_transactions(data_folder, user_attack_count):
    """Process all transaction files in a folder and aggregate MEV distribution data by attacking builder count."""
    aggregated_data = defaultdict(lambda: {"total_mev": 0, "builders_mev": 0, "users_mev": 0})

    for filename in os.listdir(data_folder):
        if filename.startswith("pbs_transactions") and f"users{user_attack_count}" in filename:
            # Extract the number of attacking builders from the filename
            try:
                builder_attack_count = int(filename.split("builders")[1].split("_")[0])
            except (IndexError, ValueError):
                print(f"Skipping file {filename} due to naming format.")
                continue
            
            file_path = os.path.join(data_folder, filename)
            file_data = calculate_mev_distribution_from_transactions(file_path)
            
            if file_data:
                aggregated_data[builder_attack_count]["total_mev"] += file_data["total_mev"]
                aggregated_data[builder_attack_count]["builders_mev"] += file_data["builders_mev"]
                aggregated_data[builder_attack_count]["users_mev"] += file_data["users_mev"]

    return aggregated_data

def plot_mev_distribution(aggregated_data, user_attack_count, save_path):
    """Plot MEV distribution for different attacking builder configurations as percentages and print exact Gwei values."""
    builder_counts = sorted(aggregated_data.keys())
    builder_mev = [aggregated_data[count]["builders_mev"] for count in builder_counts]
    user_mev = [aggregated_data[count]["users_mev"] for count in builder_counts]
    total_mev = [aggregated_data[count]["total_mev"] for count in builder_counts]
    uncaptured_mev = [total - builder - user for total, builder, user in zip(total_mev, builder_mev, user_mev)]

    # Calculate percentages for the stack plot
    builder_mev_percent = [100 * b / t if t > 0 else 0 for b, t in zip(builder_mev, total_mev)]
    user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(uncaptured_mev, total_mev)]

    # Print exact Gwei values
    for count, total, builder, user, uncaptured in zip(builder_counts, total_mev, builder_mev, user_mev, uncaptured_mev):
        print(f"Attack Builders: {count}, Total MEV: {total} Gwei, Builders MEV: {builder} Gwei, Users MEV: {user} Gwei, Uncaptured MEV: {uncaptured} Gwei")

    # Plot as percentages
    plt.figure(figsize=(12, 6))
    plt.stackplot(builder_counts, user_mev_percent, builder_mev_percent, uncaptured_mev_percent,
                  labels=["Users MEV", "Builders MEV", "Uncaptured MEV"], colors=["blue", "red", "grey"], alpha=0.6)
    plt.xlabel("Number of Attacking Builders")
    plt.ylabel("MEV Distribution (%)")
    plt.title(f"MEV Distribution with User Attack Count: {user_attack_count}")
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()  # Close the plot to free memory

    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    output_folder = 'figures/ss'
    os.makedirs(output_folder, exist_ok=True)
    user_attack_counts = [0, 7, 14, 20]  # Modify or iterate as needed

    for user_count in user_attack_counts:
        aggregated_data = process_all_transactions(data_folder, user_count)
        save_path = os.path.join(output_folder, f"mev_distribution_user_attack_{user_count}.png")
        plot_mev_distribution(aggregated_data, user_count, save_path)
