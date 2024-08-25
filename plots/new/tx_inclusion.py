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

def plot_transaction_type_distribution(data_dir, mev_counts_to_plot):
    transactions = load_transaction_types(data_dir, mev_counts_to_plot)

    all_data = []
    
    for mev_count in mev_counts_to_plot:
        if mev_count in transactions['pbs'] and mev_count in transactions['pos']:
            for tx_type in transactions['pbs'][mev_count].index:
                all_data.append({
                    'MEV Count': mev_count,
                    'Transaction Type': tx_type,
                    'Log Count': np.log1p(transactions['pbs'][mev_count][tx_type]),
                    'Type': 'PBS'
                })
                
            for tx_type in transactions['pos'][mev_count].index:
                all_data.append({
                    'MEV Count': mev_count,
                    'Transaction Type': tx_type,
                    'Log Count': np.log1p(transactions['pos'][mev_count][tx_type]),
                    'Type': 'POS'
                })

    df = pd.DataFrame(all_data)

    plt.figure(figsize=(12, 8))
    sns.lineplot(data=df, x='MEV Count', y='Log Count', hue='Transaction Type', style='Type', markers=True, dashes=False)
    plt.title('Log-Transformed Transaction Type Distribution across MEV Counts', fontsize=20)
    plt.xlabel('MEV Count', fontsize=18)
    plt.ylabel('Log Count', fontsize=18)
    plt.legend(title='Transaction Type & System', fontsize=12)
    plt.grid(True)

    plt.savefig('figures/new/transaction_type_distribution_lineplot.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/vary_mev'
    mev_counts_to_plot = [1, 25, 50] 
    plot_transaction_type_distribution(data_dir, mev_counts_to_plot)
