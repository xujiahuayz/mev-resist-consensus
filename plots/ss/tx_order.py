import os
import csv
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.ticker as ticker

def inversionen(arr):
    """
    Divide and conquer function to count inversions in the array.
    """
    m = len(arr)
    if m < 2:
        return arr, 0

    # Divide
    x1 = arr[:m // 2]
    x2 = arr[m // 2:]

    # Conquer (recursively count inversions in both halves)
    l1, invs1 = inversionen(x1)
    l2, invs2 = inversionen(x2)

    # Combine with modified merge to count cross inversions
    merged, cross_inversions = modified_merge(l1, l2)
    return merged, invs1 + invs2 + cross_inversions

def modified_merge(l1, l2):
    """
    Merge two sorted lists and count cross inversions.
    """
    m1, m2 = len(l1), len(l2)
    merged = []
    i, j = 0, 0
    cross_inversions = 0
    
    while i < m1 and j < m2:
        if l1[i] <= l2[j]:
            merged.append(l1[i])
            i += 1
        else:
            merged.append(l2[j])
            cross_inversions += m1 - i  # Count inversions
            j += 1

    # Append remaining elements
    merged.extend(l1[i:])
    merged.extend(l2[j:])
    return merged, cross_inversions

def calculate_inversion_count(transactions_by_block):
    """
    Calculate the inversion count for transaction IDs compared to a perfectly ordered list.
    """
    ids = []
    
    for block_transactions in transactions_by_block:
        for tx in block_transactions:
            tx_id = int(tx['id'])
            ids.append(tx_id)
    
    # Generate the ordered list for comparison
    ordered_list = list(range(len(ids)))

    # Use inversionen function to calculate inversion count between ids and ordered_list
    _, inversion_count = inversionen(ids)
    return inversion_count

def process_file(file_path):
    """
    Process a single CSV file to group transactions by blocks and compute the inversion count.
    """
    transactions_by_block = defaultdict(list)
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            block_number = int(row['included_at'])
            transactions_by_block[block_number].append(row)
    
    sorted_blocks = [transactions_by_block[block] for block in sorted(transactions_by_block.keys())]
    
    # Compute inversion count
    inversion_count = calculate_inversion_count(sorted_blocks)
    return inversion_count

def process_all_files(data_folder):
    """
    Process all transaction files in a folder for different builder and user configurations.
    """
    results = {}
    
    for filename in os.listdir(data_folder):
        if filename.startswith("pbs_transactions") or filename.startswith("pos_transactions"):
            parts = filename.split("_")
            
            # Handle different naming conventions for builders (PBS) and validators (PoS)
            if "builders" in parts[2]:
                builder_attack_count = int(parts[2].replace("builders", ""))
            elif "validators" in parts[2]:
                builder_attack_count = int(parts[2].replace("validators", ""))
            else:
                print(f"Skipping file {filename} due to unexpected format.")
                continue
            
            user_attack_count = int(parts[3].replace("users", "").split(".")[0])

            file_path = os.path.join(data_folder, filename)
            inversion_count = process_file(file_path)
            
            if user_attack_count not in results:
                results[user_attack_count] = {}
            results[user_attack_count][builder_attack_count] = inversion_count

    return results

def plot_heatmap(results, title, vmin, vmax, output_folder, x_label):
    """
    Plot a heatmap of inversion counts for each user and builder configuration with the same color scale.
    """
    df = pd.DataFrame(results).T.sort_index(ascending=False).sort_index(axis=1)

    plt.figure(figsize=(12, 10))
    sns.heatmap(df, annot=False, fmt=".0f", cmap="YlGnBu", cbar_kws={'label': "Inversion Count"}, vmin=vmin, vmax=vmax)
    plt.xlabel(x_label, fontsize=30)
    plt.ylabel(r"$\%$ of $U_i$: $\tau_{U_i} = \mathtt{attack}$", fontsize=30)
    plt.xticks(ticks=[0, 5, 10, 15, 20], labels=[0, 25, 50, 75, 100], fontsize=26)
    plt.yticks(ticks=[0, 10, 20, 30, 40, 50], labels=[0, 20, 40, 60, 80, 100], fontsize=26)

    plt.gca().invert_yaxis()
    
    # Access the color bar and customize its label and tick size
    cbar = plt.gca().collections[0].colorbar
    cbar.set_label("Inversion Count", size=26)
    cbar.ax.tick_params(labelsize=24)

    # Format the color bar tick labels to make them more readable, e.g., from 1e8 to 100M
    cbar.formatter = ticker.FuncFormatter(lambda x, _: f'{int(x / 1e6):,}M')
    cbar.update_ticks()

    plt.tight_layout()
    
    output_path = os.path.join(output_folder, f"{title.replace(' ', '_').lower()}.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Heatmap saved to {output_path}")

if __name__ == "__main__":
    pos_data_folder = 'data/same_seed/pos_visible80'
    pbs_data_folder = 'data/same_seed/pbs_visible80'
    output_folder = 'figures/ss'
    os.makedirs(output_folder, exist_ok=True)

    # Calculate inversion counts for each configuration for PoS and PBS
    pos_results = process_all_files(pos_data_folder)
    pbs_results = process_all_files(pbs_data_folder)

    # Determine shared color scale limits
    all_inversion_counts = [count for user_counts in pos_results.values() for count in user_counts.values()]
    all_inversion_counts += [count for user_counts in pbs_results.values() for count in user_counts.values()]
    vmin, vmax = min(all_inversion_counts), max(all_inversion_counts)

    # Plot heatmap of results for PoS with "Validators" as x-axis label
    plot_heatmap(pos_results, "Inversion Counts for PoS", vmin, vmax, output_folder, r"$\%$ of $V_i$: $\tau_{V_i} = \mathtt{attack}$")

    # Plot heatmap of results for PBS with "Builders" as x-axis label
    plot_heatmap(pbs_results, "Inversion Counts for PBS", vmin, vmax, output_folder, r"$\%$ of $B_i$: $\tau_{B_i} = \mathtt{attack}$")
