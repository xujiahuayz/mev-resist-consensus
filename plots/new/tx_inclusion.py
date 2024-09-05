import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import seaborn as sns

# Constants
MEV_BUILDER_COUNTS = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
DATA_DIRECTORIES = ['data/100_runs', 'data/100run_attackall', 'data/100run_attacknon']

def load_transaction_level_data(data_dir, mev_counts):
    """Load transaction-level data for both PBS and PoS systems."""
    transaction_data = {'pbs': [], 'pos': []}
    for mev_count in mev_counts:
        for run_id in range(1, 11):
            # Load PBS transactions
            pbs_file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'all_transactions', 'all_transactions.csv')
            if os.path.exists(pbs_file_path):
                df_pbs = pd.read_csv(pbs_file_path)
                transaction_data['pbs'].append(df_pbs)
            else:
                print(f"File not found: {pbs_file_path}")

            # Load PoS transactions
            pos_file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'all_transactions', 'all_transactions.csv')
            if os.path.exists(pos_file_path):
                df_pos = pd.read_csv(pos_file_path)
                transaction_data['pos'].append(df_pos)
            else:
                print(f"File not found: {pos_file_path}")

    return transaction_data

def calculate_mev_statistics(transaction_data):
    """Calculate the desired MEV transaction statistics for PBS and PoS."""
    stats = {'pbs': {'success_percentage': [], 'attack_percentage': []},
             'pos': {'success_percentage': [], 'attack_percentage': []}}

    for system in ['pbs', 'pos']:
        for df in transaction_data[system]:
            # Check if the DataFrame is empty
            if df.empty:
                print(f"No data for {system}")
                continue

            # Calculate percentage of user-initiated MEV transactions that succeeded
            successful_attacks = df[(df['transaction_type'] == 'attack') & (df['successful_' + system])]
            failed_attacks = df[(df['transaction_type'] == 'attack') & (~df['successful_' + system])]
            if len(successful_attacks) + len(failed_attacks) > 0:
                success_percentage = len(successful_attacks) / (len(successful_attacks) + len(failed_attacks)) * 100
            else:
                success_percentage = np.nan
            stats[system]['success_percentage'].append(success_percentage)

            # Calculate percentage of attack transactions in the block
            attack_transactions = df[(df['transaction_type'] == 'attack') | (df['transaction_type'] == 'b_attack')]
            if len(df) > 0:
                attack_percentage = len(attack_transactions) / len(df) * 100
            else:
                attack_percentage = np.nan
            stats[system]['attack_percentage'].append(attack_percentage)

    # Convert lists to arrays for easier averaging
    for key in stats:
        for metric in stats[key]:
            if len(stats[key][metric]) > 0:
                stats[key][metric] = np.array(stats[key][metric]).reshape(len(MEV_BUILDER_COUNTS), -1).mean(axis=1)
            else:
                stats[key][metric] = np.full(len(MEV_BUILDER_COUNTS), np.nan)

    return stats

def plot_mev_statistics(stats, output_file_prefix):
    """Generate the plots for MEV transaction statistics."""
    sns.set(style='darkgrid')  # Set Seaborn style

    for metric, metric_label in zip(['success_percentage', 'attack_percentage'],
                                    ['Percentage of Successful User-Initiated MEV Transactions',
                                     'Percentage of Attack Transactions in the Block']):
        plt.figure(figsize=(10, 6))

        # Plot PBS data
        plt.plot(MEV_BUILDER_COUNTS, stats['pbs'][metric], label='PBS', marker='o', color='blue', linewidth=2)

        # Plot PoS data
        plt.plot(MEV_BUILDER_COUNTS, stats['pos'][metric], label='PoS', marker='o', color='orange', linewidth=2)

        # Labels and Title
        plt.xlabel('Number of MEV Builders/Validators', fontsize=16)
        plt.ylabel(metric_label, fontsize=16)
        plt.xticks(fontsize=14)
        plt.yticks(fontsize=14)
        plt.legend(fontsize=14)
        plt.grid(axis='y')

        # Save the plot with appropriate naming
        file_name_suffix = output_file_prefix.split('/')[-1]
        plt.savefig(f'{output_file_prefix}_{metric}_{file_name_suffix}.png')
        plt.close()

if __name__ == "__main__":
    for data_dir in DATA_DIRECTORIES:
        transaction_data = load_transaction_level_data(data_dir, MEV_BUILDER_COUNTS)
        stats = calculate_mev_statistics(transaction_data)

        # Determine the suffix based on the data directory name
        if 'attackall' in data_dir:
            suffix = 'all'
        elif 'attacknon' in data_dir:
            suffix = 'none'
        else:
            suffix = '50'

        output_prefix = f'figures/new/censorship/{os.path.basename(data_dir)}'
        plot_mev_statistics(stats, f'{output_prefix}_{suffix}')
