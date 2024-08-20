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

            # Assuming transaction type is stored in a column named 'transaction_type'
            pbs_transaction_types = pbs_df['transaction_type'].value_counts()
            pos_transaction_types = pos_df['transaction_type'].value_counts()

            transactions['pbs'][mev_count] = pbs_transaction_types
            transactions['pos'][mev_count] = pos_transaction_types
        else:
            print(f"Files for MEV count {mev_count} not found. Skipping...")

    return transactions

def plot_transaction_type_distribution(data_dir, mev_counts_to_plot):
    transactions = load_transaction_types(data_dir, mev_counts_to_plot)

    fig, axes = plt.subplots(1, len(mev_counts_to_plot), figsize=(18, 6), sharey=True)

    for i, mev_count in enumerate(mev_counts_to_plot):
        if mev_count in transactions['pbs'] and mev_count in transactions['pos']:
            pbs_transactions = transactions['pbs'][mev_count]
            pos_transactions = transactions['pos'][mev_count]

            combined_data = pd.DataFrame({
                'type': ['PBS'] * len(pbs_transactions) + ['POS'] * len(pos_transactions),
                'Transaction Type': list(pbs_transactions.index) + list(pos_transactions.index),
                'Count': list(pbs_transactions.values) + list(pos_transactions.values)
            })

            # Apply log transformation to the counts for better visualization
            combined_data['Log Count'] = np.log1p(combined_data['Count'])

            sns.barplot(x='Transaction Type', y='Log Count', hue='type', data=combined_data, ax=axes[i], palette="Set3")
            axes[i].set_title(f'MEV Count = {mev_count}', fontsize=20)
            axes[i].set_xlabel('Transaction Type', fontsize=18)
            axes[i].tick_params(axis='both', which='major', labelsize=14)
            axes[i].set_ylabel('Log Count' if i == 0 else '', fontsize=18)

    plt.tight_layout()
    plt.savefig('figures/new/transaction_type_distribution.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/vary_mev'
    mev_counts_to_plot = [1, 25, 50]  # You can adjust the MEV counts to plot here
    plot_transaction_type_distribution(data_dir, mev_counts_to_plot)
