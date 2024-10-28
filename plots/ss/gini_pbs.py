import csv
import os
import re
import numpy as np
import matplotlib.pyplot as plt

def get_builder_counts(file_path):
    """Extract builder selection counts from a CSV file."""
    builder_counts = {}
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            builder_id = row['builder_id']
            if builder_id in builder_counts:
                builder_counts[builder_id] += 1
            else:
                builder_counts[builder_id] = 1
    return list(builder_counts.values())

def calculate_gini(counts):
    """Calculate the Gini coefficient for a list of counts."""
    if len(counts) == 0:
        return 0
    counts = np.array(sorted(counts))
    cumulative_counts = np.cumsum(counts)
    sum_counts = cumulative_counts[-1]
    n = len(counts)
    gini = (n + 1 - 2 * (np.sum(cumulative_counts) / sum_counts)) / n
    return gini

def parse_filename(filename):
    """Parse the filename to extract builder and user attack counts."""
    # Use regular expression to match the pattern
    match = re.search(r'builders(\d+)_users(\d+)', filename)
    if match:
        try:
            builder_attack_count = int(match.group(1))
            user_attack_count = int(match.group(2))
            return builder_attack_count, user_attack_count
        except ValueError:
            print(f"Could not parse builder or user attack counts from filename: {filename}")
    else:
        print(f"Skipping file with unexpected format: {filename}")
    return None, None

def compute_gini_coefficients(data_folder, user_attack_count):
    """Calculate Gini coefficients for a given user attack count."""
    gini_values = []
    builder_attack_counts = []

    for filename in sorted(os.listdir(data_folder)):
        if filename.startswith("pbs_block_data"):
            builder_attack_count, file_user_attack_count = parse_filename(filename)
            if file_user_attack_count == user_attack_count:
                builder_attack_counts.append(builder_attack_count)
                file_path = os.path.join(data_folder, filename)
                builder_counts = get_builder_counts(file_path)
                gini_coefficient = calculate_gini(builder_counts)
                gini_values.append(gini_coefficient)
                print(f"File: {filename}, Builders: {builder_attack_count}, Users: {file_user_attack_count}, Gini: {gini_coefficient}")

    if builder_attack_counts and gini_values:
        builder_attack_counts, gini_values = zip(*sorted(zip(builder_attack_counts, gini_values)))

    return builder_attack_counts, gini_values

def calculate_average_gini(data_folder):
    """Calculate the average Gini coefficient for all files in the folder."""
    gini_values = []

    for filename in sorted(os.listdir(data_folder)):
        if filename.startswith("pbs_block_data"):
            file_path = os.path.join(data_folder, filename)
            builder_counts = get_builder_counts(file_path)
            gini_coefficient = calculate_gini(builder_counts)
            gini_values.append(gini_coefficient)
            print(f"File: {filename}, Gini: {gini_coefficient}")

    # Calculate and print the average Gini coefficient
    if gini_values:
        average_gini = np.mean(gini_values)
        print(f"\nAverage Gini Coefficient across all files: {average_gini:.4f}")
    else:
        print("No Gini coefficients calculated.")

def plot_gini_coefficients_per_user_attack(data_folder):
    """Generate plots of Gini coefficients for different user attack counts."""
    user_attack_counts = [0, 10, 20, 30, 40, 50]
    plt.figure(figsize=(15, 10))

    for i, user_attack_count in enumerate(user_attack_counts):
        builder_attack_counts, gini_values = compute_gini_coefficients(data_folder, user_attack_count)
        
        if not builder_attack_counts or not gini_values:
            print(f"No data to plot for user attack count: {user_attack_count}")
            continue
        
        plt.subplot(2, 3, i + 1)
        plt.plot(builder_attack_counts, gini_values, marker='o', linestyle='-', color='b')
        plt.xlabel('Number of Attacking Builders')
        plt.ylabel('Gini Coefficient')
        plt.title(f'User Attack Count: {user_attack_count}')
    
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    plot_gini_coefficients_per_user_attack(data_folder)
    calculate_average_gini(data_folder)
