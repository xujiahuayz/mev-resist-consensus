import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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
            for run_id in range(1, 51):  # Adjust based on number of runs
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

def plot_gini_with_confidence(data_dir, mev_counts, output_file):
    profits = load_profits(data_dir, mev_counts)
    gini_stats = calculate_gini_statistics(profits)

    gini_pbs = [gini_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts]
    gini_pos = [gini_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[0] for mc in mev_counts]
    lower_ci_pbs = [gini_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[1] for mc in mev_counts]
    upper_ci_pbs = [gini_stats['pbs'].get(mc, (np.nan, np.nan, np.nan))[2] for mc in mev_counts]
    lower_ci_pos = [gini_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[1] for mc in mev_counts]
    upper_ci_pos = [gini_stats['pos'].get(mc, (np.nan, np.nan, np.nan))[2] for mc in mev_counts]

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.lineplot(x=mev_counts, y=gini_pbs, label='PBS', ax=ax)
    sns.lineplot(x=mev_counts, y=gini_pos, label='POS', ax=ax)
    ax.fill_between(mev_counts, lower_ci_pbs, upper_ci_pbs, color='blue', alpha=0.2, label='95% CI')
    ax.fill_between(mev_counts, lower_ci_pos, upper_ci_pos, color='orange', alpha=0.2, label='95% CI')

    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=20)
    ax.set_ylabel('Gini Coefficient', fontsize=20)
    ax.tick_params(axis='both', which='major', labelsize=18)
    ax.legend(fontsize=18)
    ax.grid(True)
    ax.xaxis.grid(True)
    ax.yaxis.grid(True)
    ax.xaxis.grid(False)
    ax.yaxis.grid(True, which='both', linestyle='--', linewidth=0.7)

    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    mev_counts = list(range(1, 51))
    data_dir = 'data/100_runs'
    plot_gini_with_confidence(data_dir, mev_counts, 'figures/new/smooth_gini_coefficient.png')
    data_dir_attackall = 'data/100run_attackall'
    plot_gini_with_confidence(data_dir_attackall, mev_counts, 'figures/new/smooth_gini_coefficient_attackall.png')
    data_dir_attacknon = 'data/100run_attacknon'
    plot_gini_with_confidence(data_dir_attacknon, mev_counts, 'figures/new/smooth_gini_coefficient_attacknon.png')
