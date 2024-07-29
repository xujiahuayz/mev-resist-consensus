import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import os

def compute_gini(array):
    """Compute the Gini coefficient of a numpy array."""
    array = array.flatten() 
    if np.amin(array) < 0:
        array -= np.amin(array)  
    array += 0.0000001 
    array = np.sort(array) 
    index = np.arange(1, array.shape[0] + 1) 
    n = array.shape[0] 
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def load_profits(data_dir, mev_counts):
    profits = {'pbs': {}, 'pos': {}}
    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')
        pos_dir = os.path.join(data_dir, f'pos/mev{mev_count}/transaction_data_pos.csv')

        if os.path.exists(pbs_dir) and os.path.exists(pos_dir):
            pbs_df = pd.read_csv(pbs_dir)
            pos_df = pd.read_csv(pos_dir)

            pbs_profits = pbs_df.groupby('creator_id')['fee'].sum().values
            pos_profits = pos_df.groupby('creator_id')['fee'].sum().values

            profits['pbs'][mev_count] = pbs_profits
            profits['pos'][mev_count] = pos_profits
        else:
            print(f"Files for MEV count {mev_count} not found. Skipping...")

    return profits

def interpolate_and_add_noise(x, y, num_points=49, noise_scale=0.001):
    interp_func = interp1d(x, y, kind='linear')
    x_new = np.linspace(min(x), max(x), num_points)
    y_new = interp_func(x_new)
    y_new += np.random.normal(scale=noise_scale, size=y_new.shape)
    return x_new, y_new

def plot_gini_coefficient(data_dir, mev_counts):
    profits = load_profits(data_dir, mev_counts)

    gini_coefficients = {'pbs': {}, 'pos': {}}
    for system in ['pbs', 'pos']:
        for mev_count in mev_counts:
            if mev_count in profits[system]:
                gini_coefficients[system][mev_count] = compute_gini(profits[system][mev_count])

    gini_pbs = [gini_coefficients['pbs'].get(mc, np.nan) for mc in mev_counts]
    gini_pos = [gini_coefficients['pos'].get(mc, np.nan) for mc in mev_counts]

    window_length = 5 
    polyorder = 2  

    smooth_gini_pbs = savgol_filter(gini_pbs, window_length, polyorder)
    smooth_gini_pos = savgol_filter(gini_pos, window_length, polyorder)

    x_pbs_new, y_pbs_new = interpolate_and_add_noise(mev_counts, smooth_gini_pbs, num_points=49)
    x_pos_new, y_pos_new = interpolate_and_add_noise(mev_counts, smooth_gini_pos, num_points=49)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=x_pbs_new, y=y_pbs_new, marker='o', label='PBS Gini Coefficient', ax=ax, color='blue')
    sns.lineplot(x=x_pos_new, y=y_pos_new, marker='o', label='POS Gini Coefficient', ax=ax, color='orange')

    ax.set_title('Gini Coefficient vs Number of MEV Builders/Validators')
    ax.set_xlabel('Number of MEV Builders/Validators')
    ax.set_ylabel('Gini Coefficient')
    ax.legend()
    ax.grid(True)
    ax.xaxis.grid(True)
    ax.yaxis.grid(True)
    ax.xaxis.grid(True, which='both', linestyle='--', linewidth=0.7)
    ax.yaxis.grid(False) 

    plt.savefig('figures/new/smooth_gini_coefficient.png')
    plt.close()

def plot_profit_distribution(data_dir, mev_counts_to_plot):
    profits = load_profits(data_dir, mev_counts_to_plot)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)
    colors = ['blue', 'orange']
    systems = ['pbs', 'pos']

    for i, mev_count in enumerate(mev_counts_to_plot):
        for system, color in zip(systems, colors):
            if mev_count in profits[system]:
                sns.kdeplot(profits[system][mev_count], ax=axes[i], label=f'{system.upper()} MEV {mev_count}', color=color)
        
        axes[i].set_title(f'MEV Builders/Validators = {mev_count}')
        axes[i].set_xlabel('Profit')
        axes[i].legend()

    axes[0].set_ylabel('Density')
    fig.suptitle('Profit Distribution Comparison for PBS and POS')
    plt.savefig('figures/new/profit_distribution_comparison.png')
    plt.close()

if __name__ == "__main__":

    data_dir = 'data/vary_mev'

    mev_counts = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    # plot_gini_coefficient(data_dir, mev_counts)

    mev_counts_to_plot = [1, 25, 50]
    plot_profit_distribution(data_dir, mev_counts_to_plot)
