import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import savgol_filter
import os

sns.set_theme(style="whitegrid")

# Ensure the output directory exists
os.makedirs('figures/theory', exist_ok=True)

# Function to calculate Gini coefficient
def gini_coefficient(profits):
    sorted_profits = np.sort(profits)
    n = len(profits)
    cumulative_profits = np.cumsum(sorted_profits, dtype=float)
    cumulative_profits /= cumulative_profits[-1]
    index = np.arange(1, n + 1)
    return (np.sum((2 * index - n - 1) * cumulative_profits)) / (n * np.sum(cumulative_profits))

# Parameters
num_builders = 50
num_simulations = 50  # Number of simulation runs
mev_counts = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]  # Number of MEV builders/validators to test

# Function to load and calculate profits
def load_profits(data_dir, mev_counts):
    profits = {'pbs': {mev_count: [] for mev_count in mev_counts},
               'pos': {mev_count: [] for mev_count in mev_counts}}
    
    for mev_count in mev_counts:
        for run in range(1, 51):  # Loop through each run (adjusted to 50 runs)
            for system in ['pbs', 'pos']:
                run_dir = os.path.join(data_dir, f'run{run}/mev{mev_count}/{system}')
                file_path = os.path.join(run_dir, 'transaction_data_pbs.csv' if system == 'pbs' else 'transaction_data_pos.csv')

                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['fee'] = pd.to_numeric(df['fee'], errors='coerce')
                    profits_data = df.groupby('creator_id')['fee'].sum().values

                    # Remove negative profits and NaNs
                    profits_data = profits_data[np.isfinite(profits_data) & (profits_data >= 0)]

                    # Ensure only top 50 profits are selected if there are more than 50 builders
                    if len(profits_data) > num_builders:
                        profits_data = np.sort(profits_data)[-num_builders:]  # Keep the largest 50 values

                    # Make sure we account for all 50 builders, including those with zero profits
                    full_profits = np.zeros(num_builders)
                    full_profits[:len(profits_data)] = profits_data
                    profits[system][mev_count].append(full_profits)
                else:
                    print(f"File not found for run {run}, MEV count {mev_count}, system {system}. Skipping...")
    
    return profits

def plot_gini_coefficient(data_dir, mev_counts):
    profits = load_profits(data_dir, mev_counts)

    gini_coefficients = {'pbs': [], 'pos': []}

    for system in ['pbs', 'pos']:
        for mev_count in mev_counts:
            total_ginis = []
            for profit_distribution in profits[system][mev_count]:
                gini = gini_coefficient(profit_distribution)
                total_ginis.append(gini)

            gini_coefficients[system].append(np.mean(total_ginis))

    # Apply smoothing
    gini_values_smooth_pbs = savgol_filter(gini_coefficients['pbs'], window_length=5, polyorder=2)
    gini_values_smooth_pos = savgol_filter(gini_coefficients['pos'], window_length=5, polyorder=2)

    # Plot the comparison
    plt.figure(figsize=(10, 6))
    plt.plot(mev_counts, gini_values_smooth_pbs, label='PBS', marker='o', color='blue')
    plt.plot(mev_counts, gini_values_smooth_pos, label='PoS', marker='o', color='orange')
    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Gini Coefficient', fontsize=20)
    plt.legend(fontsize=18)
    plt.grid(True)
    plt.title("Gini Coefficient of Builder/Validator Selection")
    plt.savefig('figures/theory/gini_compare_pos_pbs.png')
    plt.show()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    plot_gini_coefficient(data_dir, mev_counts)
