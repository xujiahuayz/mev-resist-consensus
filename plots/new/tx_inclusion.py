import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_theme(style="whitegrid")

def load_transaction_types(data_dir, mev_counts):
    transactions = {'pbs': {}, 'pos': {}}

    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')
        pos_dir = os.path.join(data_dir, f'pos/mev{mev_count}/transaction_data_pos.csv')

        if os.path.exists(pbs_dir) and os.path.exists(pos_dir):
            pbs_df = pd.read_csv(pbs_dir)
            pos_df = pd.read_csv(pos_dir)

            pbs_df['transaction_type'] = pbs_df['transaction_type'].replace('b_attack', 'attack')
            pos_df['transaction_type'] = pos_df['transaction_type'].replace('b_attack', 'attack')

            pbs_transaction_types = pbs_df['transaction_type'].value_counts()
            pos_transaction_types = pos_df['transaction_type'].value_counts()

            transactions['pbs'][mev_count] = pbs_transaction_types
            transactions['pos'][mev_count] = pos_transaction_types
        else:
            print(f"Files for MEV count {mev_count} not found. Skipping...")

    return transactions

def plot_stacked_bar_transaction_distribution(data_dir, mev_counts_to_plot):
    transactions = load_transaction_types(data_dir, mev_counts_to_plot)

    # Prepare the data for stacked bar plots
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

    # Log-transform the counts
    pbs_df = np.log1p(pbs_df)
    pos_df = np.log1p(pos_df)

    # Create the plots with the same y-axis scale for comparison
    fig, axes = plt.subplots(2, 1, figsize=(14, 12), sharex=True, sharey=True)

    pbs_df.plot(kind='bar', stacked=True, ax=axes[0], colormap='Set3')
    axes[0].set_title('Log-Transformed Transaction Type Distribution in PBS', fontsize=20)
    axes[0].set_ylabel('Log Count', fontsize=18)
    axes[0].legend(title='Transaction Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    pos_df.plot(kind='bar', stacked=True, ax=axes[1], colormap='Set3')
    axes[1].set_title('Log-Transformed Transaction Type Distribution in POS', fontsize=20)
    axes[1].set_xlabel('MEV Count', fontsize=18)
    axes[1].set_ylabel('Log Count', fontsize=18)
    axes[1].legend(title='Transaction Type', bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.tight_layout()
    plt.savefig('figures/new/log_stacked_transaction_distribution_pbs_pos.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/vary_mev'
    mev_counts_to_plot = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50] 
    plot_stacked_bar_transaction_distribution(data_dir, mev_counts_to_plot)

    