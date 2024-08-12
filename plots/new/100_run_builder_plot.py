import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os

# Function to calculate Gini coefficient
def gini_coefficient(data):
    sorted_data = np.sort(data)
    n = len(data)
    cumulative_data = np.cumsum(sorted_data, dtype=float)
    cumulative_data /= cumulative_data[-1]
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * cumulative_data)) / (n * np.sum(cumulative_data))

# Function to load builder selection data from the 100 runs
def load_selection_data(data_dir, mev_counts):
    selection_data = {}
    for mev_count in mev_counts:
        all_selections = []
        for run_id in range(1, 101):
            file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'pbs', 'block_data_pbs.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                selected_ids = df['builder_id'].values
                all_selections.append(selected_ids)
        
        if all_selections:
            selection_data[mev_count] = all_selections
        else:
            selection_data[mev_count] = []
    return selection_data

# Function to calculate Gini statistics
def calculate_gini_statistics(selection_data):
    gini_stats = {}
    for mev_count, runs in selection_data.items():
        gini_values = []
        for run in runs:
            unique, counts = np.unique(run, return_counts=True)
            gini = gini_coefficient(counts)
            gini_values.append(gini)
        
        if gini_values:
            mean_gini = np.mean(gini_values)
            lower_ci = np.percentile(gini_values, 2.5)
            upper_ci = np.percentile(gini_values, 97.5)
            gini_stats[mev_count] = (mean_gini, lower_ci, upper_ci)
        else:
            gini_stats[mev_count] = (np.nan, np.nan, np.nan)
    return gini_stats

# Function to plot Gini coefficient
def plot_gini_coefficient(gini_stats, mev_counts):
    mean_gini = [gini_stats[mc][0] for mc in mev_counts]
    lower_ci = [gini_stats[mc][1] for mc in mev_counts]
    upper_ci = [gini_stats[mc][2] for mc in mev_counts]

    plt.figure(figsize=(10, 6))
    plt.errorbar(mev_counts, mean_gini, yerr=[(top-bot)/2 for bot, top in zip(lower_ci, upper_ci)], label='PBS', color='blue', fmt='-o')
    plt.xlabel('Number of MEV Builders')
    plt.ylabel('Gini Coefficient')
    plt.title('Gini Coefficient of Builder Selection in PBS')
    plt.legend()
    plt.grid(True)
    plt.savefig('figures/new/gini_coefficient_pbs.png')
    plt.close()

# Main execution
if __name__ == "__main__":
    data_dir = 'data/100_runs'
    mev_counts = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

    selection_data_pbs = load_selection_data(data_dir, mev_counts)
    gini_stats_pbs = calculate_gini_statistics(selection_data_pbs)
    plot_gini_coefficient(gini_stats_pbs, mev_counts)
