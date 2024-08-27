import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_theme(style="whitegrid")

def load_and_aggregate_transaction_types(data_dir, mev_counts, num_runs):
    transactions = {'pbs': {}, 'pos': {}}

    for mev_count in mev_counts:
        pbs_aggregated = pd.Series(dtype='float64')
        pos_aggregated = pd.Series(dtype='float64')

        for run_id in range(1, num_runs + 1):
            pbs_dir = os.path.join(data_dir, f'run{run_id}/mev{mev_count}/pbs/transaction_data_pbs.csv')
            pos_dir = os.path.join(data_dir, f'run{run_id}/mev{mev_count}/pos/transaction_data_pos.csv')

            if os.path.exists(pbs_dir) and os.path.exists(pos_dir):
                pbs_df = pd.read_csv(pbs_dir)
                pos_df = pd.read_csv(pos_dir)

                pbs_df['transaction_type'] = pbs_df['transaction_type'].replace({'b_attack': 'attack', 'normal': 'benign', 'failed': 'failed attack'})
                pos_df['transaction_type'] = pos_df['transaction_type'].replace({'b_attack': 'attack', 'normal': 'benign', 'failed': 'failed attack'})

                # Aggregate transaction types across runs
                pbs_transaction_types = pbs_df['transaction_type'].value_counts(normalize=True) * 100
                pos_transaction_types = pos_df['transaction_type'].value_counts(normalize=True) * 100

                pbs_aggregated = pbs_aggregated.add(pbs_transaction_types, fill_value=0)
                pos_aggregated = pos_aggregated.add(pos_transaction_types, fill_value=0)
            else:
                print(f"Files for MEV count {mev_count} in run {run_id} not found. Skipping...")

        # Average the percentages over the number of runs
        transactions['pbs'][mev_count] = pbs_aggregated / num_runs
        transactions['pos'][mev_count] = pos_aggregated / num_runs

    return transactions

def plot_smooth_stacked_transaction_distribution(data_dir, mev_counts_to_plot, num_runs):
    transactions = load_and_aggregate_transaction_types(data_dir, mev_counts_to_plot, num_runs)

    # Prepare the data for stacked area plots
    pbs_data = []
    pos_data = []

    for mev_count in mev_counts_to_plot:
        if mev_count in transactions['pbs'] and mev_count in transactions['pos']:
            pbs_data.append({
                'MEV Count': mev_count,
                **transactions['pbs'][mev_count]
            })
            pos_data.append({
                'MEV Count': mev_count,
                **transactions['pos'][mev_count]
            })

    # Convert to DataFrames for easier plotting
    pbs_df = pd.DataFrame(pbs_data).set_index('MEV Count').fillna(0)
    pos_df = pd.DataFrame(pos_data).set_index('MEV Count').fillna(0)

    # Set larger font sizes
    plt.rc('axes', titlesize=24, labelsize=20)  # Titles and labels
    plt.rc('xtick', labelsize=18)
    plt.rc('ytick', labelsize=18)
    plt.rc('legend', fontsize=18)  # Legend font size

    # Create the smooth stacked area plots
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True, sharey=True)

    pbs_df.plot(kind='area', stacked=True, ax=axes[0], colormap='Set3')
    axes[0].set_ylabel('Number of Transactions (%)', fontsize=20)
    axes[0].legend(title='Transaction Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    pos_df.plot(kind='area', stacked=True, ax=axes[1], colormap='Set3')
    axes[1].set_xlabel('MEV Builder/Validator Number', fontsize=20)
    axes[1].set_ylabel('Number of Transactions (%)', fontsize=20)
    axes[1].legend(title='Transaction Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig('figures/new/average_smooth_transaction_distribution_pbs_pos.png')
    plt.close()

    # Save separate plots for PBS and POS
    pbs_df.plot(kind='area', stacked=True, figsize=(14, 8), colormap='Set3')
    plt.ylabel('Number of Transactions (%)', fontsize=20)
    plt.xlabel('MEV Builder/Validator Number', fontsize=20)
    plt.legend(title='Transaction Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('figures/new/average_smooth_transaction_distribution_pbs.png')
    plt.close()

    pos_df.plot(kind='area', stacked=True, figsize=(14, 8), colormap='Set3')
    plt.ylabel('Number of Transactions (%)', fontsize=20)
    plt.xlabel('MEV Builder/Validator Number', fontsize=20)
    plt.legend(title='Transaction Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('figures/new/average_smooth_transaction_distribution_pos.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    mev_counts_to_plot = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    num_runs = 50
    plot_smooth_stacked_transaction_distribution(data_dir, mev_counts_to_plot, num_runs)
