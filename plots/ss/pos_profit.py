import csv
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def calculate_mev_distribution_from_transactions(file_path):
    """Calculate MEV distribution among validators and users from a single transaction CSV file."""
    required_fields = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        
        if not required_fields.issubset(reader.fieldnames):
            print(f"Skipping file {file_path} due to missing fields.")
            return None

        mev_data = {"total_mev": 0, "validators_mev": 0, "users_mev": 0}
        
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
                            if 'validator' in closest_tx['creator_id']:
                                mev_data["validators_mev"] += share
                            else:
                                mev_data["users_mev"] += share
            except (ValueError, KeyError) as e:
                print(f"Error in processing transaction: {e}")

    return mev_data

def process_all_transactions(data_folder, user_attack_count, cache_file, file_prefix):
    """Process all transaction files in a folder and aggregate MEV distribution data by attacking validator count."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    aggregated_data = defaultdict(lambda: {"total_mev": 0, "validators_mev": 0, "users_mev": 0})

    for filename in os.listdir(data_folder):
        if filename.startswith(file_prefix) and f"users{user_attack_count}" in filename:
            try:
                validator_attack_count = int(filename.split("validators")[1].split("_")[0])
            except (IndexError, ValueError):
                print(f"Skipping file {filename} due to naming format.")
                continue
            
            file_path = os.path.join(data_folder, filename)
            file_data = calculate_mev_distribution_from_transactions(file_path)
            
            if file_data:
                for key in file_data:
                    aggregated_data[validator_attack_count][key] += file_data[key]

    with open(cache_file, 'w') as f:
        json.dump(aggregated_data, f)

    return aggregated_data

def smooth_data(data, window_size=3):
    """Apply a more robust smoothing, specifically for percentages to keep them within range."""
    smoothed_data = np.convolve(data, np.ones(window_size) / window_size, mode='same')
    smoothed_data[0], smoothed_data[-1] = data[0], data[-1]  # Ensure edge values are kept the same
    return smoothed_data

def plot_mev_distribution(aggregated_data, user_attack_count, save_path, role):
    counts = sorted(aggregated_data.keys())
    role_mev = [aggregated_data[count][f"{role}_mev"] for count in counts]
    user_mev = [aggregated_data[count]["users_mev"] for count in counts]
    total_mev = [aggregated_data[count]["total_mev"] for count in counts]
    uncaptured_mev = [total - role_val - user for total, role_val, user in zip(total_mev, role_mev, user_mev)]

    # Calculate percentages
    role_mev_percent = [100 * r / t if t > 0 else 0 for r, t in zip(role_mev, total_mev)]
    user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(uncaptured_mev, total_mev)]

    # Apply smoothing without altering the 0 and max counts
    smooth_role_mev = smooth_data(role_mev_percent)
    smooth_user_mev = smooth_data(user_mev_percent)
    smooth_uncaptured_mev = smooth_data(uncaptured_mev_percent)

    # Ensure all stacks add to 100% after smoothing
    total_smoothed = smooth_role_mev + smooth_user_mev + smooth_uncaptured_mev
    smooth_role_mev = smooth_role_mev / total_smoothed * 100
    smooth_user_mev = smooth_user_mev / total_smoothed * 100
    smooth_uncaptured_mev = smooth_uncaptured_mev / total_smoothed * 100

    plt.figure(figsize=(8, 8))

    plt.stackplot(counts, smooth_user_mev, smooth_role_mev, smooth_uncaptured_mev,
                  labels=["Users MEV", f"{role.capitalize()} MEV", "Uncaptured MEV"], colors=["blue", "red", "grey"], alpha=0.6)
    
    plt.xlabel(f"Number of Attacking {role.capitalize()}s", fontsize=20)
    plt.ylabel("MEV Profit Distribution (%)", fontsize=20)
    plt.title(f"MEV Profit Distribution with User Attack Count: {user_attack_count}", fontsize=24)
    plt.legend(loc="upper right", fontsize=14)
    plt.xticks(ticks=[0, 5, 10, 15, 20], labels=[0, 5, 10, 15, 20], fontsize=14)
    plt.yticks(fontsize=14)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    data_folders = {
        "pbs": "data/same_seed/pbs_visible80",
        "pos": "data/same_seed/pos_visible80"
    }
    output_folder = 'figures/ss'
    os.makedirs(output_folder, exist_ok=True)
    user_attack_counts = [0, 12, 24, 50]

    for system, data_folder in data_folders.items():
        file_prefix = "pbs_transactions" if system == "pbs" else "pos_transactions"
        role = "builder" if system == "pbs" else "validator"
        
        for user_count in user_attack_counts:
            cache_file = os.path.join(output_folder, f"{system}_aggregated_data_user_attack_{user_count}.json")
            aggregated_data = process_all_transactions(data_folder, user_count, cache_file, file_prefix)
            save_path = os.path.join(output_folder, f"{system}_mev_distribution_user_attack_{user_count}.png")
            plot_mev_distribution(aggregated_data, user_count, save_path, role)
