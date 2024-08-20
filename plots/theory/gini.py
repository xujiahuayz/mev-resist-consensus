import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import norm
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
num_simulations = 100  # Number of simulation runs
mu_mev = 10
sigma_mev = 2
mu_gas = 5
sigma_gas = 1

# Number of MEV builders/validators
mev_builders_range = np.arange(1, num_builders + 1)

# Store Gini coefficients for theoretical PBS
gini_values_theory = []

# Simulate and calculate Gini coefficients (Theoretical)
for mev_builders in mev_builders_range:
    non_mev_builders = num_builders - mev_builders
    gini_coeffs = []
    for _ in range(num_simulations):
        mev_profits = norm.rvs(loc=mu_mev, scale=sigma_mev, size=mev_builders)
        gas_profits = norm.rvs(loc=mu_gas, scale=sigma_gas, size=non_mev_builders)
        total_profits = np.concatenate((mev_profits, gas_profits))
        gini_coeffs.append(gini_coefficient(total_profits))
    gini_values_theory.append(np.mean(gini_coeffs))

# Apply Savitzky-Golay filter for smoothing (Theoretical)
gini_values_smooth_theory = savgol_filter(gini_values_theory, window_length=7, polyorder=2)

# Function to compute Gini coefficient from CSV files (Simulation)
def compute_gini(array):
    array = array.astype(float).flatten()
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 0.0000001
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def load_profits(data_dir, mev_counts):
    profits = {'pbs': {}}
    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')

        if os.path.exists(pbs_dir):
            pbs_df = pd.read_csv(pbs_dir)
            pbs_df['fee'] = pd.to_numeric(pbs_df['fee'], errors='coerce')

            pbs_profits = pbs_df.groupby('creator_id')['fee'].sum().values
            # Remove negative profits and NaNs
            pbs_profits = pbs_profits[np.isfinite(pbs_profits) & (pbs_profits >= 0)]

            profits['pbs'][mev_count] = pbs_profits
        else:
            print(f"Files for MEV count {mev_count} not found. Skipping...")

    return profits

def plot_gini_coefficient(data_dir, mev_counts, gini_values_smooth_theory, mev_builders_range):
    profits = load_profits(data_dir, mev_counts)

    gini_coefficients_pbs = []

    for mev_count in mev_counts:
        if mev_count in profits['pbs']:
            total_ginis = []
            for _ in range(num_simulations):
                selected_builders = np.zeros(num_builders)
                profits_pbs = profits['pbs'][mev_count]

                if len(profits_pbs) < num_builders:
                    # If fewer builders are selected, the rest have zero profits
                    full_profits = np.concatenate((profits_pbs, np.zeros(num_builders - len(profits_pbs))))
                else:
                    full_profits = profits_pbs

                gini = gini_coefficient(full_profits)
                total_ginis.append(gini)

            gini_coefficients_pbs.append(np.mean(total_ginis))

    # Apply smoothing
    gini_values_smooth_pbs = savgol_filter(gini_coefficients_pbs, window_length=5, polyorder=2)

    # Plot the comparison
    plt.figure(figsize=(10, 6))
    plt.plot(mev_builders_range, gini_values_smooth_theory, label='PBS (Theoretical)', color='red', linestyle='--')
    plt.plot(mev_counts, gini_values_smooth_pbs, label='PBS (Simulation)', marker='o')
    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Gini Coefficient', fontsize=20)
    plt.legend(fontsize=18)
    plt.grid(True)
    plt.savefig('figures/theory/gini_compare.png')
    plt.show()

if __name__ == "__main__":
    # Theoretical part
    num_builders = 50
    mev_builders_range = np.arange(1, num_builders + 1)

    # Simulated part
    data_dir = 'data/vary_mev'
    mev_counts = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

    plot_gini_coefficient(data_dir, mev_counts, gini_values_smooth_theory, mev_builders_range)
