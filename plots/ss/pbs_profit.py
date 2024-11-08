import csv
import os
import json
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def calculate_mev_distribution_from_transactions(file_path):
    """Calculate MEV distribution among builders and users from a single transaction CSV file."""
    required_fields = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        
        if not required_fields.issubset(reader.fieldnames):
            print(f"Skipping file {file_path} due to missing fields.")
            return None

        mev_data = {"total_mev": 0, "builders_mev": 0, "users_mev": 0}
        
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
                                mev_data["builders_mev"] += share
                            else:
                                mev_data["users_mev"] += share
            except (ValueError, KeyError) as e:
                print(f"Error in processing transaction: {e}")

    return mev_data

def process_all_transactions(data_folder, user_attack_count, cache_file):
    """Process all transaction files in a folder and aggregate MEV distribution data by attacking builder count."""
    # Load from cache if available
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as f:
            return json.load(f)

    aggregated_data = defaultdict(lambda: {"total_mev": 0, "builders_mev": 0, "users_mev": 0})

    for filename in os.listdir(data_folder):
        if filename.startswith("pbs_transactions") and f"users{user_attack_count}" in filename:
            try:
                builder_attack_count = int(filename.split("builders")[1].split("_")[0])
            except (IndexError, ValueError):
                print(f"Skipping file {filename} due to naming format.")
                continue
            
            file_path = os.path.join(data_folder, filename)
            file_data = calculate_mev_distribution_from_transactions(file_path)
            
            if file_data:
                for key in file_data:
                    aggregated_data[builder_attack_count][key] += file_data[key]

    # Save results to cache for future use
    with open(cache_file, 'w') as f:
        json.dump(aggregated_data, f)

    return aggregated_data

def smooth_data(data, window_size=3):
    """Apply a moving average to smooth data."""
    return np.convolve(data, np.ones(window_size) / window_size, mode='valid')

def plot_mev_distribution(aggregated_data, user_attack_count, save_path):
    """Plot MEV distribution for different attacking builder configurations as percentages and print exact Gwei values."""
    title_font_size = 22  # Larger font for titles
    label_font_size = 20  # Larger font for axis labels
    legend_font_size = 16  # Larger font for legend
    tick_label_font_size = 16  # Larger font for axis tick labels

    builder_counts = sorted(aggregated_data.keys())
    builder_mev = [aggregated_data[count]["builders_mev"] for count in builder_counts]
    user_mev = [aggregated_data[count]["users_mev"] for count in builder_counts]
    total_mev = [aggregated_data[count]["total_mev"] for count in builder_counts]
    uncaptured_mev = [total - builder - user for total, builder, user in zip(total_mev, builder_mev, user_mev)]

    builder_mev_percent = [100 * b / t if t > 0 else 0 for b, t in zip(builder_mev, total_mev)]
    user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(uncaptured_mev, total_mev)]

    # Apply additional smoothing if user_attack_count is 50
    if user_attack_count == 50:
        smooth_builder_mev = smooth_data(smooth_data(builder_mev_percent))
        smooth_user_mev = smooth_data(smooth_data(user_mev_percent))
        smooth_uncaptured_mev = smooth_data(smooth_data(uncaptured_mev_percent))
        builder_counts = builder_counts[len(builder_counts) - len(smooth_user_mev):]
    else:
        smooth_builder_mev = builder_mev_percent
        smooth_user_mev = user_mev_percent
        smooth_uncaptured_mev = uncaptured_mev_percent

    print("Exact Gwei Values:")
    for count, total, builder, user, uncaptured in zip(builder_counts, total_mev, builder_mev, user_mev, uncaptured_mev):
        print(f"Attack Builders: {count}, Total MEV: {total} Gwei, Builders MEV: {builder} Gwei, Users MEV: {user} Gwei, Uncaptured MEV: {uncaptured} Gwei")

    plt.figure(figsize=(10, 8))
    plt.stackplot(builder_counts, smooth_user_mev, smooth_builder_mev, smooth_uncaptured_mev,
                  labels=["Users MEV", "Builders MEV", "Uncaptured MEV"], colors=["blue", "red", "grey"], alpha=0.6)
    plt.xlabel("Number of Attacking Builders", fontsize=label_font_size)
    plt.ylabel("MEV Profit Distribution (%)", fontsize=label_font_size)
    plt.title(f"MEV Profit Distribution with User Attack Count: {user_attack_count}", fontsize=title_font_size)
    plt.legend(loc="upper right", fontsize=legend_font_size)
    plt.xticks(fontsize=tick_label_font_size)
    plt.yticks(fontsize=tick_label_font_size)
    plt.margins(x=0, y=0)
    plt.tight_layout(pad=1.0)
    plt.savefig(save_path, dpi=300, bbox_inches='tight')
    plt.close()

    print(f"Plot saved to {save_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    output_folder = 'figures/ss'
    os.makedirs(output_folder, exist_ok=True)
    user_attack_counts = [0, 12, 24, 50]

    for user_count in user_attack_counts:
        cache_file = os.path.join(output_folder, f"aggregated_data_user_attack_{user_count}.json")
        aggregated_data = process_all_transactions(data_folder, user_count, cache_file)
        save_path = os.path.join(output_folder, f"mev_distribution_user_attack_{user_count}.png")
        plot_mev_distribution(aggregated_data, user_count, save_path)
