import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_theme(style="whitegrid")

def load_transaction_data(data_dir, mev_counts):
    inclusion_times = {'pbs': {}, 'pos': {}}
    attack_inclusion_probabilities = {'pbs': {}, 'pos': {}}

    for mev_count in mev_counts:
        for system in ['pbs', 'pos']:
            all_times = {'normal': [], 'mev': [], 'attack': []}
            total_attack_tx = 0
            included_attack_tx = 0

            for run_id in range(1, 51):  # Adjust according to the number of runs
                mev_dir = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}')
                file_path = os.path.join(mev_dir, 'all_transactions', 'all_transactions.csv')

                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)

                    # Ensure inclusion columns are present
                    if 'included_pbs' not in df.columns or 'included_pos' not in df.columns:
                        continue

                    included_column = 'included_pbs' if system == 'pbs' else 'included_pos'
                    inclusion_time_column = 'pbs_inclusion_time' if system == 'pbs' else 'pos_inclusion_time'

                    # Time to inclusion for different types of transactions
                    for tx_type in ['normal', 'mev', 'attack']:
                        times = df[(df['transaction_type'] == tx_type) & (df[included_column].astype(bool))][inclusion_time_column].dropna().values
                        all_times[tx_type].extend(times)

                    # Calculate the inclusion probability for user-initiated attack transactions
                    attack_tx = df[(df['transaction_type'] == 'attack') & (df['mev_potential'] > 0)]
                    total_attack_tx += len(attack_tx)
                    included_attack_tx += len(attack_tx[attack_tx[included_column].astype(bool)])

            inclusion_times[system][mev_count] = {tx_type: all_times[tx_type] for tx_type in all_times}
            attack_inclusion_probabilities[system][mev_count] = (included_attack_tx / total_attack_tx) * 100 if total_attack_tx > 0 else 0

    return inclusion_times, attack_inclusion_probabilities

def plot_inclusion_time_for_specific_mev_counts(data_dir, mev_counts, output_file):
    inclusion_times, _ = load_transaction_data(data_dir, mev_counts)

    # Define the specific MEV counts to plot
    specific_mev_counts = [0, 25, 50]

    plt.figure(figsize=(12, 8))
    for system in ['pbs', 'pos']:
        for tx_type in ['normal', 'mev', 'attack']:
            for mc in specific_mev_counts:
                if mc in inclusion_times[system]:
                    times = inclusion_times[system][mc][tx_type]
                    plt.plot([mc] * len(times), times, 'o', label=f'{system.upper()} - {tx_type.capitalize()} (MEV {mc})', alpha=0.7)

    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Number of Blocks Taken to Inclusion', fontsize=20)
    plt.legend(fontsize=14, loc='upper left')
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

def plot_attack_inclusion_probability_for_specific_mev_counts(data_dir, mev_counts, output_file):
    _, attack_inclusion_probabilities = load_transaction_data(data_dir, mev_counts)

    specific_mev_counts = [0, 25, 50]
    prob_pbs = [attack_inclusion_probabilities['pbs'].get(mc, 0) for mc in specific_mev_counts]
    prob_pos = [attack_inclusion_probabilities['pos'].get(mc, 0) for mc in specific_mev_counts]

    plt.figure(figsize=(10, 6))
    plt.plot(specific_mev_counts, prob_pbs, '-o', label='PBS', color='blue')
    plt.plot(specific_mev_counts, prob_pos, '-o', label='POS', color='orange')
    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Probability of Attack Transaction Inclusion (%)', fontsize=20)
    plt.legend(fontsize=18)
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    mev_counts = list(range(1, 51))
    data_dir_default = 'data/100_runs'

    # Plot the number of blocks taken for inclusion
    plot_inclusion_time_for_specific_mev_counts(data_dir_default, mev_counts, 'figures/new/inclusion_time_specific.png')

    # Plot the probability of user-initiated attack transactions being included in the final block
    plot_attack_inclusion_probability_for_specific_mev_counts(data_dir_default, mev_counts, 'figures/new/attack_inclusion_probability_specific.png')
