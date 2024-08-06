import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import os

sns.set_theme(style="whitegrid")

def compute_gini(array):
    """Compute the Gini coefficient of a numpy array."""
    array = array.astype(float).flatten()
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 0.0000001  # To avoid division by zero
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def load_profits(data_dir, mev_counts):
    profits = {'pbs': {}, 'pos': {}}
    for mev_count in mev_counts:
        for system in ['pbs', 'pos']:
            run_profits = []
            for run_id in range(1, 51):
                file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', system, f'transaction_data_{system}.csv')
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['fee'] = pd.to_numeric(df['fee'], errors='coerce')
                    df['mev_captured'] = pd.to_numeric(df['mev_captured'], errors='coerce')
                    if 'block_bid' in df.columns:
                        df['block_bid'] = pd.to_numeric(df['block_bid'], errors='coerce', downcast='float')
                    else:
                        df['block_bid'] = 0

                    if system == 'pbs':
                        df['profit'] = df['fee'] + df['mev_captured'] - df['block_bid']
                    elif system == 'pos':
                        df['profit'] = df['fee'] + df['mev_captured']

                    proposer_profits = df.groupby('creator_id')['profit'].sum().values
                    run_profits.append(proposer_profits)

            if len(run_profits) > 0:
                run_profits = [profits[np.isfinite(profits) & (profits >= 0)] for profits in run_profits if len(profits) > 0]
                profits[system][mev_count] = run_profits
            else:
                profits[system][mev_count] = np.array([])

    return profits

def calculate_gini_statistics(profits):
    gini_stats = {'pbs': {}, 'pos': {}}
    for system in ['pbs', 'pos']:
        for mev_count, runs in profits[system].items():
            gini_values = [compute_gini(run) for run in runs if len(run) > 0]
            if gini_values:
                mean_gini = np.mean(gini_values)
                lower_ci = np.percentile(gini_values, 2.5)
                upper_ci = np.percentile(gini_values, 97.5)
                gini_stats[system][mev_count] = (mean_gini, lower_ci, upper_ci)
            else:
                gini_stats[system][mev_count] = (np.nan, np.nan, np.nan)
    return gini_stats

def interpolate_and_smooth(x, y, num_points=49, window_length=5, polyorder=2):
    interp_func = interp1d(x, y, kind='linear', fill_value="extrapolate")
    x_new = np.linspace(min(x), max(x), num_points)
    y_new = interp_func(x_new)
    y_smooth = savgol_filter(y_new, window_length, polyorder)
    return x_new, y_smooth

def plot_gini_with_confidence(data_dir, mev_counts):
    profits = load_profits(data_dir, mev_counts)
    gini_stats = calculate_gini_statistics(profits)

    gini_pbs = [gini_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts]
    gini_pos = [gini_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts]
    lower_ci_pbs = [gini_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[1] for mc in mev_counts]
    upper_ci_pbs = [gini_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[2] for mc in mev_counts]
    lower_ci_pos = [gini_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[1] for mc in mev_counts]
    upper_ci_pos = [gini_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[2] for mc in mev_counts]

    valid_indices_pbs = [i for i, val in enumerate(gini_pbs) if not np.isnan(val)]
    valid_indices_pos = [i for i, val in enumerate(gini_pos) if not np.isnan(val)]

    x_pbs, y_pbs = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pbs], np.array(gini_pbs)[valid_indices_pbs])
    x_pos, y_pos = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pos], np.array(gini_pos)[valid_indices_pos])
    _, lower_ci_pbs_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pbs], np.array(lower_ci_pbs)[valid_indices_pbs])
    _, upper_ci_pbs_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pbs], np.array(upper_ci_pbs)[valid_indices_pbs])
    _, lower_ci_pos_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pos], np.array(lower_ci_pos)[valid_indices_pos])
    _, upper_ci_pos_smooth = interpolate_and_smooth(np.array(mev_counts)[valid_indices_pos], np.array(upper_ci_pos)[valid_indices_pos])

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=x_pbs, y=y_pbs, label='PBS', ax=ax)
    sns.lineplot(x=x_pos, y=y_pos, label='POS', ax=ax)
    ax.fill_between(x_pbs, lower_ci_pbs_smooth, upper_ci_pbs_smooth, color='blue', alpha=0.2, label='95% CI')
    ax.fill_between(x_pos, lower_ci_pos_smooth, upper_ci_pos_smooth, color='orange', alpha=0.2, label='95% CI')

    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=20)
    ax.set_ylabel('Gini Coefficient', fontsize=20)
    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.legend(fontsize=18)
    ax.grid(True)
    ax.xaxis.grid(True)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, which='both', linestyle='--', linewidth=0.7)

    plt.savefig('figures/new/smooth_gini_coefficient.png')
    plt.close()

def plot_total_profits(data_dir, mev_counts):
    total_profits = {'pbs': {'mev': [], 'non_mev': []}, 'pos': {'mev': [], 'non_mev': []}}
    
    for mev_count in mev_counts:
        for system in ['pbs', 'pos']:
            mev_profits = []
            non_mev_profits = []
            
            for run_id in range(1, 51):
                file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', system, f'transaction_data_{system}.csv')
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    df['fee'] = pd.to_numeric(df['fee'], errors='coerce')
                    df['mev_captured'] = pd.to_numeric(df['mev_captured'], errors='coerce')
                    if 'block_bid' in df.columns:
                        df['block_bid'] = pd.to_numeric(df['block_bid'], errors='coerce', downcast='float')
                    else:
                        df['block_bid'] = 0

                    if system == 'pbs':
                        df['profit'] = df['fee'] + df['mev_captured'] - df['block_bid']
                    elif system == 'pos':
                        df['profit'] = df['fee'] + df['mev_captured']

                    for creator_id, profit in df.groupby('creator_id')['profit'].sum().items():
                        if creator_id <= mev_count:
                            mev_profits.append(profit)
                        else:
                            non_mev_profits.append(profit)
            
            total_profits[system]['mev'].append(np.sum(mev_profits))
            total_profits[system]['non_mev'].append(np.sum(non_mev_profits))
    
    fig, ax = plt.subplots(figsize=(10, 6))
    width = 0.35
    indices = np.arange(len(mev_counts))

    bars_pbs_mev = ax.bar(indices - width/2, total_profits['pbs']['mev'], width, label='PBS MEV', color='blue')
    bars_pos_mev = ax.bar(indices + width/2, total_profits['pos']['mev'], width, label='POS MEV', color='orange')
    bars_pbs_non_mev = ax.bar(indices - width/2, total_profits['pbs']['non_mev'], width, bottom=total_profits['pbs']['mev'], color='lightblue', label='PBS Non-MEV')
    bars_pos_non_mev = ax.bar(indices + width/2, total_profits['pos']['non_mev'], width, bottom=total_profits['pos']['mev'], color='lightcoral', label='POS Non-MEV')

    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=20)
    ax.set_ylabel('Total Profits', fontsize=20)
    ax.set_xticks(indices)
    ax.set_xticklabels([1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50], fontsize=18)
    ax.legend(fontsize=18)
    ax.grid(True)
    ax.xaxis.grid(True)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, which='both', linestyle='--', linewidth=0.7)

    plt.title('Total Profits of MEV and Non-MEV Builders/Validators', fontsize=22)
    plt.savefig('figures/new/total_profits_bar_chart.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    mev_counts = list(range(1, 51))
    plot_gini_with_confidence(data_dir, mev_counts)
    plot_total_profits(data_dir, mev_counts)
