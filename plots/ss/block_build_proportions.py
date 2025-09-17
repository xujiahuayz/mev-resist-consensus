import csv
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from matplotlib import ticker

# Constants
TOTAL_VALIDATORS = 20
TOTAL_BUILDERS = 20
TOTAL_USERS = 50

def get_final_percentages(file_path, attack_count):
    """Extract final cumulative percentages at the end of the simulation."""
    attacking_total = 0
    non_attacking_total = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Extract numeric part of ID
            if 'validator_id' in row:
                entity_id = int(row['validator_id'].split('_')[-1])
            elif 'builder_id' in row:
                entity_id = int(row['builder_id'].split('_')[-1])
            else:
                continue
                
            # Count attacker vs. non-attacker
            if entity_id < attack_count:
                attacking_total += 1
            else:
                non_attacking_total += 1
    
    total = attacking_total + non_attacking_total
    if total == 0:
        return 0, 0
    
    attacking_pct = (attacking_total / total) * 100
    non_attacking_pct = (non_attacking_total / total) * 100
    
    return attacking_pct, non_attacking_pct

def process_all_files(data_folder_path, system_type):
    """
    Process all block data files in a folder for different builder/validator and user configurations.
    Returns a dictionary with attacking percentages for each configuration.
    """
    results = {}
    
    for filename in os.listdir(data_folder_path):
        if filename.startswith(f"{system_type}_block_data"):
            parts = filename.split("_")
            
            # Extract validator/builder count and user count
            if "validators" in parts[3]:
                entity_attack_count = int(parts[3].replace("validators", ""))
            elif "builders" in parts[3]:
                entity_attack_count = int(parts[3].replace("builders", ""))
            else:
                continue
                
            user_attack_count = int(parts[4].replace("users", "").split(".")[0])
            
            file_path = os.path.join(data_folder_path, filename)
            attacking_pct, non_attacking_pct = get_final_percentages(file_path, entity_attack_count)
            
            if user_attack_count not in results:
                results[user_attack_count] = {}
            results[user_attack_count][entity_attack_count] = attacking_pct
    
    return results

def plot_heatmap(results, title, output_folder_path, x_label, y_label, system_type):
    """
    Plot a heatmap of attacking percentages for each user and builder/validator configuration.
    """
    df = pd.DataFrame(results).T.sort_index(ascending=False).sort_index(axis=1)
    
    # Create the heatmap - exactly like tx_order.py
    # Adjust figure size based on whether color bar is present
    if "pbs" in system_type.lower():
        plt.figure(figsize=(12, 10))  # Wider to accommodate color bar
    else:
        plt.figure(figsize=(10, 10))  # Square when no color bar
    
    # Only show color bar for PBS plot
    if "pbs" in system_type.lower():
        sns.heatmap(df, annot=False, fmt=".0f", cmap="YlGnBu", cbar_kws={'label': "Blocks built by attacking participants (%)"}, vmin=0, vmax=100)
    else:
        sns.heatmap(df, annot=False, fmt=".0f", cmap="YlGnBu", cbar=False, vmin=0, vmax=100)
    
    plt.xlabel(x_label, fontsize=36)
    plt.ylabel(y_label, fontsize=36)
    plt.xticks(ticks=[0, 5, 10, 15, 20], labels=[0, 25, 50, 75, 100], fontsize=36)
    plt.yticks(ticks=[0, 10, 20, 30, 40, 50], labels=[0, 20, 40, 60, 80, 100], fontsize=36)
    
    plt.gca().invert_yaxis()
    
    # Force y-axis labels to be horizontal like x-axis
    plt.gca().tick_params(axis='y', labelrotation=0)
    
    # Access the color bar and customize its label and tick size (only for PBS plot)
    if "pbs" in system_type.lower():
        cbar = plt.gca().collections[0].colorbar
        cbar.set_label("Blocks built by attacking participants (%)", size=36)
        cbar.ax.tick_params(labelsize=36)
    
    plt.tight_layout()
    
    # Save the heatmap
    output_path = os.path.join(output_folder_path, f"{title.replace(' ', '_').lower()}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to {output_path}")

def create_heatmap_visualization():
    """Create heatmap visualizations for POS and PBS showing attacking percentages across all configurations."""
    # Set seaborn style to match tx_order.py
    sns.set_style("whitegrid")
    plt.rcParams['xtick.labelsize'] = 28
    plt.rcParams['ytick.labelsize'] = 28
    plt.rcParams['xtick.direction'] = 'inout'
    plt.rcParams['ytick.direction'] = 'inout'
    
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)
    
    # Data paths
    pos_data_folder = 'data/same_seed/pos_visible80'
    pbs_data_folder = 'data/same_seed/pbs_visible80'
    
    print("Processing POS data...")
    pos_results = process_all_files(pos_data_folder, "pos")
    
    print("Processing PBS data...")
    pbs_results = process_all_files(pbs_data_folder, "pbs")
    
    # Plot POS heatmap
    plot_heatmap(
        pos_results, 
        "pos_block_build_proportions", 
        output_dir,
        r"Validators $\tau_{V_i} = \mathtt{attack}$ (%)",
        r"Users $\tau_{U_i} = \mathtt{attack}$ (%)",
        "pos"
    )
    
    # Plot PBS heatmap
    plot_heatmap(
        pbs_results, 
        "pbs_block_build_proportions", 
        output_dir,
        r"Builders $\tau_{B_i} = \mathtt{attack}$ (%)",
        r"Users $\tau_{U_i} = \mathtt{attack}$ (%)",
        "pbs"
    )
    
    # Print summary statistics
    print(f"\nProcessed {len(pos_results)} user configurations for POS")
    print(f"Processed {len(pbs_results)} user configurations for PBS")
    print(f"Each configuration has {len(list(pos_results.values())[0])} entity configurations")
    print("Heatmaps saved successfully!")

if __name__ == "__main__":
    create_heatmap_visualization() 
    