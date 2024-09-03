import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

sns.set_theme(style="whitegrid")

def load_transaction_data(data_dir, mev_counts):
    inclusion_probabilities = {'pbs': {}, 'pos': {}}
    inclusion_times = {'pbs': {}, 'pos': {}}

    for mev_count in mev_counts:
        for system in ['pbs', 'pos']:
            all_inclusion_data = []
            all_times = {'normal': [], 'mev': [], 'attack': []}

            for run_id in range(1, 51):
                file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'all_transactions', 'all_transactions.csv')
                if os.path.exists(file_path):
                    df = pd.read_csv(file_path)
                    # Filter user-initiated MEV transactions
                    mev_user_tx = df[(df['mev_potential'] > 0) & (df['transaction_type'] == 'mev')]

                    # Determine which column to use for inclusion check
                    included_column = 'included_pbs' if system == 'pbs' else 'included_pos'
                    
                    # Calculate probability of inclusion for MEV transactions
                    included_mev = mev_user_tx[mev_user_tx[included_column]]
                    probability_inclusion = len(included_mev) / len(mev_user_tx) if len(mev_user_tx) > 0 else 0
                    all_inclusion_data.append(probability_inclusion)

                    # Time to inclusion for different types of transactions
                    inclusion_time_column = 'pbs_inclusion_time' if system == 'pbs' else 'pos_inclusion_time'
                    for tx_type in ['normal', 'mev', 'attack']:
                        times = df[df['transaction_type'] == tx_type][inclusion_time_column].dropna().values
                        all_times[tx_type].extend(times)

            inclusion_probabilities[system][mev_count] = np.mean(all_inclusion_data) if all_inclusion_data else 0
            inclusion_times[system][mev_count] = {tx_type: np.mean(all_times[tx_type]) for tx_type in all_times}

    return inclusion_probabilities, inclusion_times

def plot_mev_inclusion_probability(data_dir, mev_counts, output_file):
    inclusion_probabilities, _ = load_transaction_data(data_dir, mev_counts)

    prob_pbs = [inclusion_probabilities['pbs'].get(mc, 0) for mc in mev_counts]
    prob_pos = [inclusion_probabilities['pos'].get(mc, 0) for mc in mev_counts]

    plt.figure(figsize=(10, 6))
    plt.plot(mev_counts, prob_pbs, label='PBS', color='blue')
    plt.plot(mev_counts, prob_pos, label='POS', color='orange')
    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Probability of Inclusion of MEV Transactions', fontsize=20)
    plt.legend(fontsize=18)
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

def plot_inclusion_time(data_dir, mev_counts, output_file):
    _, inclusion_times = load_transaction_data(data_dir, mev_counts)

    inclusion_time_data = {'pbs': {'normal': [], 'mev': [], 'attack': []}, 'pos': {'normal': [], 'mev': [], 'attack': []}}

    for system in ['pbs', 'pos']:
        for tx_type in ['normal', 'mev', 'attack']:
            for mc in mev_counts:
                inclusion_time_data[system][tx_type].append(inclusion_times[system].get(mc, {}).get(tx_type, np.nan))

    plt.figure(figsize=(12, 8))
    for tx_type in ['normal', 'mev', 'attack']:
        plt.plot(mev_counts, inclusion_time_data['pbs'][tx_type], label=f'PBS - {tx_type.capitalize()}')
        plt.plot(mev_counts, inclusion_time_data['pos'][tx_type], label=f'POS - {tx_type.capitalize()}')

    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Average Time to Inclusion', fontsize=20)
    plt.legend(fontsize=14)
    plt.grid(True)
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    mev_counts = list(range(1, 51))
    data_dir_default = 'data/100_runs'
    data_dir_attackall = 'data/100run_attackall'
    data_dir_attacknon = 'data/100run_attacknon'

    plot_mev_inclusion_probability(data_dir_default, mev_counts, 'figures/new/mev_inclusion_probability.png')
    plot_inclusion_time(data_dir_default, mev_counts, 'figures/new/inclusion_time.png')
