import os
import csv
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from collections import defaultdict

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
    print(f"File: {file_path} -> Inversion Count: {inversion_count}")  # Debug print to verify results
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

def print_results(results, label):
    """
    Print inversion counts for each configuration.
    """
    print(f"Inversion Counts ({label}):")
    for user_attack_count, builders in results.items():
        for builder_attack_count, inversions in builders.items():
            print(f"Users: {user_attack_count}, Builders/Validators: {builder_attack_count} -> Inversions: {inversions}")

def plot_heatmap(results, title):
    """
    Plot a heatmap of inversion counts for each user and builder configuration.
    """
    df = pd.DataFrame(results).T.sort_index(ascending=False).sort_index(axis=1)

    plt.figure(figsize=(10, 8))
    sns.heatmap(df, annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={'label': "Inversion Count"})
    plt.title(title)
    plt.xlabel("Number of Attacking Builders/Validators")
    plt.ylabel("Number of Attacking Users")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    pos_data_folder = 'data/same_seed/pos_visible80'  # Path to PoS data folder
    pbs_data_folder = 'data/same_seed/pbs_visible80'  # Path to PBS data folder
    
    # Calculate inversion counts for each configuration for PoS and PBS
    pos_results = process_all_files(pos_data_folder)
    pbs_results = process_all_files(pbs_data_folder)
    
    # Print the results for each system
    print_results(pos_results, "PoS")
    print_results(pbs_results, "PBS")
    
    # Plot heatmap of results for PoS
    plot_heatmap(pos_results, "Inversion Counts for PoS")

    # Plot heatmap of results for PBS
    plot_heatmap(pbs_results, "Inversion Counts for PBS")
