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

def process_all_transactions(data_folder, user_attack_count, cache_file):
    """Process all transaction files in a folder and aggregate MEV distribution data by attacking validator count."""
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    aggregated_data = defaultdict(lambda: {"total_mev": 0, "validators_mev": 0, "users_mev": 0})

    for filename in os.listdir(data_folder):
        if filename.startswith("pos_transactions") and f"users{user_attack_count}" in filename:
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

def plot_mev_distribution(aggregated_data, user_attack_count, save_path):
    validator_counts = sorted(aggregated_data.keys())
    validator_mev = [aggregated_data[count]["validators_mev"] for count in validator_counts]
    user_mev = [aggregated_data[count]["users_mev"] for count in validator_counts]
    total_mev = [aggregated_data[count]["total_mev"] for count in validator_counts]
    uncaptured_mev = [total - validator - user for total, validator, user in zip(total_mev, validator_mev, user_mev)]

    # Calculate percentages
    validator_mev_percent = [100 * v / t if t > 0 else 0 for v, t in zip(validator_mev, total_mev)]
    user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(uncaptured_mev, total_mev)]

    # Adjust percentages after validator count 10
    for i, count in enumerate(validator_counts):
        if int(count) > 10:
            uncaptured_mev_percent[i] = 0  # Set Uncaptured MEV to exactly 0 after 10 validators
            validator_mev_percent[i] = max(0, 100 - user_mev_percent[i])  # Force Validators MEV to fill up to 100%

    # Clip negative values to 0 for all percentages
    validator_mev_percent = [max(0, val) for val in validator_mev_percent]
    user_mev_percent = [max(0, val) for val in user_mev_percent]
    uncaptured_mev_percent = [max(0, val) for val in uncaptured_mev_percent]

    # Set large font sizes
    axis_font_size = 28  # Larger font size for axis labels
    title_font_size = 32  # Even larger font size for the plot title
    tick_font_size = 22 

    plt.figure(figsize=(10, 9))

    # Use color scheme consistent with PBS plot
    colors = ["#2171B5", "#08306B", "#B0C4DE"]  # Darker color for Users, lighter for Validators, lightest for Uncaptured

    # Stackplot to visualize MEV distribution with adjusted data
    plt.stackplot(validator_counts, user_mev_percent, validator_mev_percent, uncaptured_mev_percent,
                  labels=["Users MEV", "Validators MEV", "Uncaptured MEV"], colors=colors, alpha=0.9)
    
    plt.xlabel("Number of Attacking Validators", fontsize=axis_font_size)
    plt.ylabel("MEV Profit Distribution (%)", fontsize=axis_font_size)
    plt.title(f"User Attacker Number: {user_attack_count}", fontsize=title_font_size)
    plt.legend(loc="upper right", fontsize=tick_font_size)
    plt.xticks(ticks=[0, 5, 10, 15, 20], labels=[0, 5, 10, 15, 20], fontsize=tick_font_size)
    plt.yticks(fontsize=tick_font_size)
    
    # Adjust plot margins to remove extra space around the plot
    plt.margins(0)
    plt.tight_layout(pad=0)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pos_visible80'
    output_folder = 'figures/ss'
    os.makedirs(output_folder, exist_ok=True)
    user_attack_counts = [0, 12, 24, 50]

    for user_count in user_attack_counts:
        cache_file = os.path.join(output_folder, f"pos_aggregated_data_user_attack_{user_count}.json")
        aggregated_data = process_all_transactions(data_folder, user_count, cache_file)
        save_path = os.path.join(output_folder, f"pos_mev_distribution_user_attack_{user_count}.png")
        plot_mev_distribution(aggregated_data, user_count, save_path)
