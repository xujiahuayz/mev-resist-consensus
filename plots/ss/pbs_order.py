import os
import csv
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict

def calculate_spearman_coefficient(transactions_by_block):
    """
    Calculate the Spearman's rank correlation coefficient for transaction order and cumulative position.
    Each transaction's cumulative position is calculated by adding the number of transactions in all previous blocks.
    """
    cumulative_position = 0
    ids = []
    absolute_positions = []
    
    for block_transactions in transactions_by_block:
        for tx in block_transactions:
            tx_id = int(tx['id'])
            position_in_block = int(tx['position'])
            absolute_position = cumulative_position + position_in_block

            ids.append(tx_id)
            absolute_positions.append(absolute_position)
        
        # Update cumulative position by adding the count of transactions in this block
        cumulative_position += len(block_transactions)

    # Compute Spearman's rank correlation between creation order and cumulative position
    coefficient, _ = spearmanr(ids, absolute_positions)
    return coefficient

def process_file(file_path):
    """
    Process a single CSV file to group transactions by blocks and compute the Spearman coefficient.
    """
    transactions_by_block = defaultdict(list)
    
    # Read the file and group transactions by block number
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            block_number = int(row['included_at'])  # Assuming 'included_at' is the block number
            transactions_by_block[block_number].append(row)
    
    # Sort transactions by block number
    sorted_blocks = [transactions_by_block[block] for block in sorted(transactions_by_block.keys())]
    
    return calculate_spearman_coefficient(sorted_blocks)


def process_all_files(data_folder):
    """
    Process all transaction files in a folder for different builder and user configurations.
    """
    results = {}
    
    for filename in os.listdir(data_folder):
        if filename.startswith("pbs_transactions"):
            parts = filename.split("_")
            builder_attack_count = int(parts[2].replace("builders", ""))
            user_attack_count = int(parts[3].replace("users", "").split(".")[0])

            file_path = os.path.join(data_folder, filename)
            spearman_coefficient = process_file(file_path)
            
            if user_attack_count not in results:
                results[user_attack_count] = {}
            results[user_attack_count][builder_attack_count] = spearman_coefficient

    return results

def plot_heatmap(results):
    """
    Plot a heatmap of Spearman coefficients for each user and builder configuration.
    """
    # Convert results to a DataFrame for easy plotting, ensure ordered index and columns
    df = pd.DataFrame(results).T.sort_index(ascending=False).sort_index(axis=1)

    plt.figure(figsize=(10, 8))
    sns.heatmap(df, annot=True, fmt=".2f", cmap="RdYlBu", center=0, vmin=-1, vmax=1, 
                cbar_kws={'label': "Spearman Coefficient"})

    # Add axis labels
    plt.xlabel("Number of Attacking Builders")
    plt.ylabel("Number of Attacking Users")
    
    # Show plot without the title
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    
    # Calculate Spearman coefficients for each configuration
    results = process_all_files(data_folder)
    
    # Plot heatmap of results
    plot_heatmap(results)
