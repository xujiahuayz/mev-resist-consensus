import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def compute_gini(array):
    """Compute the Gini coefficient of a numpy array."""
    if array.size == 0:
        return np.nan
    array = array.flatten().astype(float)  # Ensure the array is float
    if np.amin(array) < 0:
        array -= np.amin(array)
    array += 0.0000001  # Prevent division by zero
    array = np.sort(array)
    index = np.arange(1, array.shape[0] + 1)
    n = array.shape[0]
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))

def load_data(data_dir, mev_counts):
    data = {'pbs': {}, 'pos': {}}
    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')
        pos_dir = os.path.join(data_dir, f'pos/mev{mev_count}/transaction_data_pos.csv')

        if os.path.exists(pbs_dir) and os.path.exists(pos_dir):
            pbs_df = pd.read_csv(pbs_dir)
            pos_df = pd.read_csv(pos_dir)

            if 'builder_type' not in pbs_df.columns or 'builder_type' not in pos_df.columns:
                print(f"builder_type column not found in MEV count {mev_count} files. Skipping...")
                continue

            pbs_builders = pbs_df['builder_type'].value_counts()
            pos_builders = pos_df['builder_type'].value_counts()

            data['pbs'][mev_count] = pbs_builders
            data['pos'][mev_count] = pos_builders
        else:
            print(f"Files for MEV count {mev_count} not found. Skipping...")

    return data

def plot_gini_coefficient_mev_non_mev(data_dir, mev_counts):
    data = load_data(data_dir, mev_counts)

    gini_coefficients = {'pbs_mev': [], 'pbs_non_mev': [], 'pos_mev': [], 'pos_non_mev': []}
    for system in ['pbs', 'pos']:
        for mev_count in mev_counts:
            if mev_count in data[system]:
                builder_blocks = data[system][mev_count]
                mev_blocks = builder_blocks.get('mev', 0)
                non_mev_blocks = builder_blocks.sum() - mev_blocks

                print(f"{system.upper()} MEV Count {mev_count} - MEV Blocks: {mev_blocks}, Non-MEV Blocks: {non_mev_blocks}")

                if system == 'pbs':
                    gini_coefficients['pbs_mev'].append(compute_gini(np.array([mev_blocks])))
                    gini_coefficients['pbs_non_mev'].append(compute_gini(np.array([non_mev_blocks])))
                else:
                    gini_coefficients['pos_mev'].append(compute_gini(np.array([mev_blocks])))
                    gini_coefficients['pos_non_mev'].append(compute_gini(np.array([non_mev_blocks])))

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(mev_counts, gini_coefficients['pbs_mev'], marker='o', label='PBS MEV', color='blue')
    ax.plot(mev_counts, gini_coefficients['pbs_non_mev'], marker='o', label='PBS Non-MEV', color='cyan')
    ax.plot(mev_counts, gini_coefficients['pos_mev'], marker='o', label='POS MEV', color='orange')
    ax.plot(mev_counts, gini_coefficients['pos_non_mev'], marker='o', label='POS Non-MEV', color='yellow')

    ax.set_title('Gini Coefficient of Block Creation Likelihood', fontsize=20)
    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=18)
    ax.set_ylabel('Gini Coefficient', fontsize=18)
    ax.legend(fontsize=16)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.grid(True)

    plt.savefig('figures/new/gini_coefficient_mev_non_mev.png')
    plt.close()

def plot_percentage_blocks_by_mev(data_dir, mev_counts):
    data = load_data(data_dir, mev_counts)

    percentages = {'pbs': [], 'pos': []}
    for system in ['pbs', 'pos']:
        for mev_count in mev_counts:
            if mev_count in data[system]:
                builder_blocks = data[system][mev_count]
                total_blocks = builder_blocks.sum()
                if total_blocks == 0:
                    percentages[system].append(0)
                else:
                    mev_blocks = builder_blocks.get('mev', 0)
                    percentages[system].append((mev_blocks / total_blocks) * 100)
                print(f"{system.upper()} MEV Count {mev_count} - Total Blocks: {total_blocks}, MEV Blocks: {mev_blocks}")

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(mev_counts, percentages['pbs'], marker='o', label='PBS', color='blue')
    ax.plot(mev_counts, percentages['pos'], marker='o', label='POS', color='orange')

    ax.set_title('Percentage of Blocks Built by MEV Builders/Validators', fontsize=20)
    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=18)
    ax.set_ylabel('Percentage of Blocks Built (%)', fontsize=18)
    ax.legend(fontsize=16)
    ax.tick_params(axis='both', which='major', labelsize=14)
    ax.grid(True)

    plt.savefig('figures/new/percentage_blocks_by_mev.png')
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/vary_mev'
    mev_counts = [1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
    plot_gini_coefficient_mev_non_mev(data_dir, mev_counts)
    plot_percentage_blocks_by_mev(data_dir, mev_counts)
