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

                # Filter transactions where fee > 0 (user-initiated transactions)
                pbs_df = pbs_df[pbs_df['fee'] > 0]
                pos_df = pos_df[pos_df['fee'] > 0]

                # Mapping transaction types for consistency
                pbs_df['transaction_type'] = pbs_df['transaction_type'].replace({'b_attack': 'Attack', 'normal': 'Benign', 'failed': 'Failed Attack'})
                pos_df['transaction_type'] = pos_df['transaction_type'].replace({'b_attack': 'Attack', 'normal': 'Benign', 'failed': 'Failed Attack'})

                pbs_df = pbs_df[pbs_df['fee'] != 0]
                pos_df = pos_df[pos_df['fee'] != 0]

                pbs_transaction_types = pbs_df['transaction_type'].value_counts(normalize=True) * 100
                pos_transaction_types = pos_df['transaction_type'].value_counts(normalize=True) * 100

                pbs_aggregated = pbs_aggregated.add(pbs_transaction_types, fill_value=0)
                pos_aggregated = pos_aggregated.add(pos_transaction_types, fill_value=0)
            else:
                print(f"Files for MEV count {mev_count} in run {run_id} not found. Skipping...")

        transactions['pbs'][mev_count] = pbs_aggregated / num_runs
        transactions['pos'][mev_count] = pos_aggregated / num_runs

    return transactions

def plot_stacked_transaction_distribution(data_dir, mev_counts_to_plot, num_runs):
    transactions = load_and_aggregate_transaction_types(data_dir, mev_counts_to_plot, num_runs)

    category_order = ['Benign', 'Attack', 'Failed Attack']

    for system in ['pbs', 'pos']:
        data = []
        for mev_count in mev_counts_to_plot:
            if mev_count in transactions[system]:
                data.append({
                    'MEV Count': mev_count,
                    **transactions[system][mev_count]
                })

        df = pd.DataFrame(data).set_index('MEV Count').fillna(0).reindex(columns=category_order)

        plt.rc('axes', titlesize=24, labelsize=20)
        plt.rc('xtick', labelsize=18)
        plt.rc('ytick', labelsize=18)
        plt.rc('legend', fontsize=20)

        fig, ax = plt.subplots(figsize=(14, 8))  # Adjust the figsize to match your desired scale

        df.plot(kind='area', stacked=True, ax=ax, colormap='Set3')
        ax.set_ylabel('Number of Transactions (%)', fontsize=20)
        x_label = 'MEV Builder Number' if system == 'pbs' else 'MEV Validator Number'
        ax.set_xlabel(x_label, fontsize=20)
        ax.legend(title='Transaction Type', title_fontsize=22, bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig('figures/new/average_smooth_transaction_distribution_pbs_pos.png')
    plt.close()

    # Save separate plots for PBS and POS
    pbs_df.plot(kind='area', stacked=True, figsize=(14, 8), colormap='Set3')
    plt.ylabel('Number of Transactions (%)', fontsize=20)
    plt.xlabel('MEV Builder/Validator Number', fontsize=20)
    plt.legend(title='Transaction Type', title_fontsize=22, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('figures/new/average_smooth_transaction_distribution_pbs.png')
    plt.close()

    pos_df.plot(kind='area', stacked=True, figsize=(14, 8), colormap='Set3')
    plt.ylabel('Number of Transactions (%)', fontsize=20)
    plt.xlabel('MEV Builder/Validator Number', fontSize=20)
    plt.legend(title='Transaction Type', title_fontsize=22, bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig('figures/new/average_smooth_transaction_distribution_pos.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    mev_counts_to_plot = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    num_runs = 50
    plot_stacked_transaction_distribution(data_dir, mev_counts_to_plot, num_runs)
