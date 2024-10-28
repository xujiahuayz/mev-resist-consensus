import csv
import os
import numpy as np
import matplotlib.pyplot as plt

def calculate_gini(array):
    """Calculate the Gini coefficient for an array of values."""
    array = np.array(array, dtype=np.float64)
    if array.sum() == 0:
        return 0.0
    array = np.sort(array)
    n = len(array)
    cumulative_values = np.cumsum(array)
    gini = (2.0 * np.sum((np.arange(1, n + 1) * array)) / (n * cumulative_values[-1])) - (n + 1) / n
    return gini

def get_builder_counts(file_path):
    """Count builder selections from a CSV file."""
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

def compute_gini_coefficients(data_folder):
    """Calculate Gini coefficients for all files in a directory."""
    gini_values = []
    builder_attack_counts = []

    for filename in sorted(os.listdir(data_folder)):
        if filename.startswith("pbs_block_data"):
            builder_attack_count = int(filename.split("_builders")[1].split("_")[0])  # Extract builder attack count
            builder_attack_counts.append(builder_attack_count)

            file_path = os.path.join(data_folder, filename)
            builder_counts = get_builder_counts(file_path)
            gini_coefficient = calculate_gini(builder_counts)
            gini_values.append(gini_coefficient)

    return builder_attack_counts, gini_values

def plot_gini_coefficients(builder_attack_counts, gini_values):
    """Plot Gini coefficients against the number of attacking builders."""
    plt.figure(figsize=(10, 6))
    plt.plot(builder_attack_counts, gini_values, marker='o', color='skyblue')
    plt.xlabel('Number of Attacking Builders')
    plt.ylabel('Gini Coefficient of Builder Selection')
    plt.title('Gini Coefficient of Builder Selection vs. Attacking Builders')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('figures/ss/gini_coefficient_builder_selection.png')
    plt.show()

if __name__ == "__main__":
    # Define the folder path of the CSV files
    data_folder = 'data/same_seed/pbs_visible80'

    # Compute Gini coefficients and plot
    builder_attack_counts, gini_values = compute_gini_coefficients(data_folder)
    plot_gini_coefficients(builder_attack_counts, gini_values)
