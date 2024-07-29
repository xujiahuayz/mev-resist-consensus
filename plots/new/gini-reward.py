import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def compute_gini(array):
    """Compute the Gini coefficient of a numpy array."""
    array = array.flatten()  # all values are treated as a single list
    if np.amin(array) < 0:
        array -= np.amin(array)  # values cannot be negative
    array += 0.0000001  # values cannot be 0
    array = np.sort(array)  # values must be sorted
    index = np.arange(1, array.shape[0] + 1)  # index per array element
    n = array.shape[0]  # number of array elements
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))  # Gini coefficient

def load_profits(data_dir, mev_counts):
    profits = {'pbs': {}, 'pos': {}}
    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')
        pos_dir = os.path.join(data_dir, f'pos/mev{mev_count}/transaction_data_pos.csv')

        pbs_df = pd.read_csv(pbs_dir)
        pos_df = pd.read_csv(pos_dir)

        pbs_profits = pbs_df.groupby('creator_id')['fee'].sum().values
        pos_profits = pos_df.groupby('creator_id')['fee'].sum().values

        profits['pbs'][mev_count] = pbs_profits
        profits['pos'][mev_count] = pos_profits

    return profits

# Set the directory containing the data
data_dir = 'data/vary_mev'

# Set the MEV builder counts to analyze
mev_counts = [1, 25, 50]

# Load the profits data
profits = load_profits(data_dir, mev_counts)

# Compute Gini coefficients
gini_coefficients = {'pbs': {}, 'pos': {}}
for system in ['pbs', 'pos']:
    for mev_count in mev_counts:
        gini_coefficients[system][mev_count] = compute_gini(profits[system][mev_count])
def plot_profit_distribution(profits, mev_counts, save_dir):
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('Profit Distribution for Different MEV Builders')

    for i, mev_count in enumerate(mev_counts):
        # Plot PBS profit distribution
        ax = axes[0, i]
        sns.histplot(profits['pbs'][mev_count], bins=20, kde=True, color='blue', ax=ax)
        ax.set_title(f'PBS Profit Distribution (MEV = {mev_count})')
        ax.set_xlabel('Profit')
        ax.set_ylabel('Frequency')

        # Plot PoS profit distribution
        ax = axes[1, i]
        sns.histplot(profits['pos'][mev_count], bins=20, kde=True, color='green', ax=ax)
        ax.set_title(f'PoS Profit Distribution (MEV = {mev_count})')
        ax.set_xlabel('Profit')
        ax.set_ylabel('Frequency')

    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(os.path.join(save_dir, 'profit_distribution.png'))
    plt.close()

def plot_gini_coefficients(gini_coefficients, mev_counts, save_dir):
    systems = ['pbs', 'pos']
    fig, ax = plt.subplots(figsize=(10, 6))

    for system in systems:
        gini_values = [gini_coefficients[system][mev_count] for mev_count in mev_counts]
        sns.lineplot(x=mev_counts, y=gini_values, marker='o', label=f'{system.upper()} Gini Coefficient', ax=ax)

    ax.set_title('Gini Coefficient vs Number of MEV Builders/Validators')
    ax.set_xlabel('Number of MEV Builders/Validators')
    ax.set_ylabel('Gini Coefficient')
    ax.legend()
    ax.grid(True)
    plt.savefig(os.path.join(save_dir, 'gini_coefficient.png'))
    plt.close()

# Create the save directory if it doesn't exist
save_dir = 'figures/new'
os.makedirs(save_dir, exist_ok=True)

# Plot profit distributions
plot_profit_distribution(profits, mev_counts, save_dir)

# Plot Gini coefficients
plot_gini_coefficients(gini_coefficients, mev_counts, save_dir)
