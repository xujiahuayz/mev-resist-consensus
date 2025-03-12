# import csv
# import os
# import json
# import matplotlib.pyplot as plt
# import seaborn as sns
# import numpy as np
# from collections import defaultdict
# from scipy.signal import savgol_filter  # Import Savitzky-Golay filter

# def calculate_mev_distribution_from_transactions(file_path):
#     """Calculate MEV distribution among builders and users from a single transaction CSV file."""
#     required_fields = {'mev_potential', 'id', 'position', 'creator_id', 'target_tx', 'included_at'}
    
#     with open(file_path, 'r') as f:
#         reader = csv.DictReader(f)
        
#         if not required_fields.issubset(reader.fieldnames):
#             print(f"Skipping file {file_path} due to missing fields.")
#             return None

#         mev_data = {"total_mev": 0, "builders_mev": 0, "users_mev": 0}
        
#         transactions = list(reader)
        
#         for tx in transactions:
#             try:
#                 mev_potential = int(tx['mev_potential'].strip())
#                 creator_id = tx['creator_id'].strip()
                
#                 if mev_potential > 0:
#                     mev_data["total_mev"] += mev_potential
#                     targeting_txs = [
#                         t for t in transactions if t.get('target_tx') == tx['id']
#                     ]
                    
#                     if targeting_txs:
#                         min_distance = min(abs(int(t['position']) - int(tx['position'])) for t in targeting_txs)
#                         closest_txs = [t for t in targeting_txs if abs(int(t['position']) - int(tx['position'])) == min_distance]

#                         share = mev_potential / len(closest_txs)
#                         for closest_tx in closest_txs:
#                             if 'builder' in closest_tx['creator_id']:
#                                 mev_data["builders_mev"] += share
#                             else:
#                                 mev_data["users_mev"] += share
#             except (ValueError, KeyError) as e:
#                 print(f"Error in processing transaction: {e}")

#     return mev_data

# def process_all_transactions(data_folder, user_attack_count, cache_file):
#     """Process all transaction files in a folder and aggregate MEV distribution data by attacking builder count."""
#     if os.path.exists(cache_file):
#         with open(cache_file, 'r') as f:
#             return json.load(f)

#     aggregated_data = defaultdict(lambda: {"total_mev": 0, "builders_mev": 0, "users_mev": 0})

#     for filename in os.listdir(data_folder):
#         if filename.startswith("pbs_transactions") and f"users{user_attack_count}" in filename:
#             try:
#                 builder_attack_count = int(filename.split("builders")[1].split("_")[0])
#             except (IndexError, ValueError):
#                 print(f"Skipping file {filename} due to naming format.")
#                 continue
            
#             file_path = os.path.join(data_folder, filename)
#             file_data = calculate_mev_distribution_from_transactions(file_path)
            
#             if file_data:
#                 for key in file_data:
#                     aggregated_data[builder_attack_count][key] += file_data[key]

#     with open(cache_file, 'w') as f:
#         json.dump(aggregated_data, f)

#     return aggregated_data

# def smooth_data(data, window_length=5, polyorder=2):
#     """Apply Savitzky-Golay smoothing to the data while keeping the original data points consistent."""
#     if len(data) >= window_length:
#         return savgol_filter(data, window_length, polyorder)
#     return data  # Return original data if it's too short for smoothing

# def plot_mev_distribution(aggregated_data, user_attack_count, save_path):
#     builder_counts = sorted(aggregated_data.keys())
#     builder_mev = [aggregated_data[count]["builders_mev"] for count in builder_counts]
#     user_mev = [aggregated_data[count]["users_mev"] for count in builder_counts]
#     total_mev = [aggregated_data[count]["total_mev"] for count in builder_counts]
#     uncaptured_mev = [total - builder - user for total, builder, user in zip(total_mev, builder_mev, user_mev)]

#     # Calculate percentages
#     builder_mev_percent = [100 * b / t if t > 0 else 0 for b, t in zip(builder_mev, total_mev)]
#     user_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(user_mev, total_mev)]
#     uncaptured_mev_percent = [100 * u / t if t > 0 else 0 for u, t in zip(uncaptured_mev, total_mev)]

#     # Apply smoothing
#     builder_mev_percent = smooth_data(builder_mev_percent)
#     user_mev_percent = smooth_data(user_mev_percent)
#     uncaptured_mev_percent = smooth_data(uncaptured_mev_percent)

#     # Adjust percentages after builder count 10
#     for i, count in enumerate(builder_counts):
#         if int(count) > 10:
#             uncaptured_mev_percent[i] = 0  # Set Uncaptured MEV to exactly 0 after 10 builders
#             builder_mev_percent[i] = max(0, 100 - user_mev_percent[i])  # Force Builders MEV to fill up to 100%

#     # Clip negative values to 0 for all percentages
#     builder_mev_percent = [max(0, val) for val in builder_mev_percent]
#     user_mev_percent = [max(0, val) for val in user_mev_percent]
#     uncaptured_mev_percent = [max(0, val) for val in uncaptured_mev_percent]

#     # Set large font sizes
#     axis_font_size = 28  # Larger font size for axis labels
#     title_font_size = 32  # Even larger font size for the plot title
#     tick_font_size = 22 

#     plt.figure(figsize=(10, 9))

#     # Use Seaborn Blues palette with specified shades
#     palette = sns.color_palette("Blues", 3)
#     colors = [palette[2], palette[1], palette[0]]  # Darkest to lightest: Users, Builders, Uncaptured

#     # Stackplot to visualize MEV distribution with adjusted data
#     plt.stackplot(builder_counts, user_mev_percent, builder_mev_percent, uncaptured_mev_percent,
#                   labels=["Users MEV", "Builders MEV", "Uncaptured MEV"], colors=colors, alpha=0.9)
    
#     plt.xlabel("Number of Attacking Builders", fontsize=axis_font_size)
#     plt.ylabel("MEV Profit Distribution (%)", fontsize=axis_font_size)
#     plt.title(f"User Attacker Number: {user_attack_count}", fontsize=title_font_size)
#     plt.legend(loc="upper right", fontsize=tick_font_size)
#     plt.xticks(ticks=[0, 5, 10, 15, 20], labels=[0, 5, 10, 15, 20], fontsize=tick_font_size)
#     plt.yticks(fontsize=tick_font_size)
    
#     # Adjust plot margins to remove extra space around the plot
#     plt.margins(0)
#     plt.tight_layout(pad=0)
#     plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
#     plt.close()

#     print(f"Plot saved to {save_path}")

# if __name__ == "__main__":
#     data_folder = 'data/same_seed/pbs_visible80'
#     output_folder = 'figures/ss'
#     os.makedirs(output_folder, exist_ok=True)
#     user_attack_counts = [0, 12, 24, 50]

#     for user_count in user_attack_counts:
#         cache_file = os.path.join(output_folder, f"pbs_aggregated_data_user_attack_{user_count}.json")
#         aggregated_data = process_all_transactions(data_folder, user_count, cache_file)
#         save_path = os.path.join(output_folder, f"pbs_mev_distribution_user_attack_{user_count}.png")
#         plot_mev_distribution(aggregated_data, user_count, save_path)

import json
import os
import matplotlib.pyplot as plt
import seaborn as sns

def load_data(file_path):
    """Load JSON data from a file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def plot_mev_distribution(aggregated_data, user_attack_count, save_path, total_builders=20):
    """Generate and save a plot of MEV distribution without a legend."""
    builder_counts = sorted(int(key) for key in aggregated_data.keys())
    builder_percentages = [100 * c / total_builders for c in builder_counts]
    builder_mev = [aggregated_data[str(count)]["builders_mev"] for count in builder_counts]
    user_mev = [aggregated_data[str(count)]["users_mev"] for count in builder_counts]
    total_mev = [aggregated_data[str(count)]["total_mev"] for count in builder_counts]

    builder_mev_percent = [100 * b / t if t else 0 for b, t in zip(builder_mev, total_mev)]
    user_mev_percent = [100 * u / t if t else 0 for u, t in zip(user_mev, total_mev)]
    uncaptured_mev_percent = [100 - b - u for b, u in zip(builder_mev_percent, user_mev_percent)]

    plt.figure(figsize=(10, 9))
    palette = sns.color_palette("Blues", 3)
    colors = [palette[2], palette[1], palette[0]]

    plt.stackplot(builder_percentages, user_mev_percent, builder_mev_percent, uncaptured_mev_percent,
                  colors=colors, alpha=0.9)
    
    user_attack_percentage_map = {'0': '0', '12': '33', '24': '67', '50': '100'}
    user_attack_percentage = user_attack_percentage_map.get(str(user_attack_count), 'Check Data')
    plt.xlabel("Attacking Builders (%)", fontsize=36)
    plt.ylabel("MEV Profit Distribution (%)", fontsize=36)
    plt.title(f"Attacking User: {user_attack_percentage}%", fontsize=36)
    
    plt.xticks(ticks=[0, 25, 50, 75, 100], labels=['0', '25', '50', '75', '100'], fontsize=36)
    plt.yticks(fontsize=36)
    plt.margins(0)
    plt.tight_layout(pad=0)
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

def create_legend_figure(save_path):
    """Generate and save a separate figure containing only the legend."""
    plt.figure(figsize=(10, 2))
    palette = sns.color_palette("Blues", 3)
    colors = [palette[2], palette[1], palette[0]]
    
    labels = ["Users'", "Builders'", "Uncaptured"]
    handles = [plt.Rectangle((0, 0), 1, 1, color=color) for color in colors]
    
    legend = plt.legend(handles, labels, loc='center', fontsize=36, frameon=False)
    plt.axis('off')
    
    plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0)
    plt.close()

def main():
    data_folder = '/Users/tammy/pbs/figures/ss'
    output_folder = '/Users/tammy/pbs/figures/ss'
    os.makedirs(output_folder, exist_ok=True)

    for file_name in os.listdir(data_folder):
        if file_name.endswith('.json') and file_name.startswith('pbs_aggregated_data_user_attack'):
            file_path = os.path.join(data_folder, file_name)
            data = load_data(file_path)
            user_attack_count = file_name.split('_')[-1].split('.')[0]
            save_path = os.path.join(output_folder, f"pbs_mev_distribution_user_attack_{user_attack_count}.png")
            plot_mev_distribution(data, user_attack_count, save_path)
    
    legend_path = os.path.join(output_folder, "pbs_mev_dis_legend.png")
    create_legend_figure(legend_path)

if __name__ == "__main__":
    main()
