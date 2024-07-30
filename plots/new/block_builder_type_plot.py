import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

def inspect_columns(data_dir, mev_counts):
    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')
        pos_dir = os.path.join(data_dir, f'pos/mev{mev_count}/transaction_data_pos.csv')

        if os.path.exists(pbs_dir):
            pbs_df = pd.read_csv(pbs_dir)
            print(f"MEV Count {mev_count} PBS Columns: {pbs_df.columns.tolist()}")

        if os.path.exists(pos_dir):
            pos_df = pd.read_csv(pos_dir)
            print(f"MEV Count {mev_count} POS Columns: {pos_df.columns.tolist()}")

def load_data(data_dir, mev_counts):
    data = {'pbs': {}, 'pos': {}}
    for mev_count in mev_counts:
        pbs_dir = os.path.join(data_dir, f'pbs/mev{mev_count}/transaction_data_pbs.csv')
        pos_dir = os.path.join(data_dir, f'pos/mev{mev_count}/transaction_data_pos.csv')

        if os.path.exists(pbs_dir) and os.path.exists(pos_dir):
            pbs_df = pd.read_csv(pbs_dir)
            pos_df = pd.read_csv(pos_dir)

            if 'builder_type' not in pbs_df.columns or 'builder_type' not in pos_df.columns:
                print(f"builder_type column not found in MEV count {mev_count} files. Available PBS columns: {pbs_df.columns.tolist()}, POS columns: {pos_df.columns.tolist()}. Skipping...")
                continue

            pbs_builders = pbs_df['builder_type'].value_counts()
            pos_builders = pos_df['builder_type'].value_counts()

            data['pbs'][mev_count] = pbs_builders
            data['pos'][mev_count] = pos_builders
        else:
            print(f"Files for MEV count {mev_count} not found. Skipping...")

    return data

def plot_bar_chart_for_mev(data_dir, mev_counts_to_plot):
    data = load_data(data_dir, mev_counts_to_plot)

    for mev_count in mev_counts_to_plot:
        if mev_count in data['pbs'] and mev_count in data['pos']:
            pbs_builders = data['pbs'][mev_count]
            pos_builders = data['pos'][mev_count]

            combined_data = pd.DataFrame({
                'type': ['PBS'] * len(pbs_builders) + ['POS'] * len(pos_builders),
                'Participant Type': list(pbs_builders.index) + list(pos_builders.index),
                'Number of Blocks Built': list(pbs_builders.values) + list(pos_builders.values)
            })

            plt.figure(figsize=(12, 6))
            sns.barplot(x='Participant Type', y='Number of Blocks Built', hue='type', data=combined_data)
            plt.title(f'Number of Blocks Built for MEV Count = {mev_count}', fontsize=20)
            plt.xlabel('Participant Type', fontsize=18)
            plt.ylabel('Number of Blocks Built', fontsize=18)
            plt.legend(title='Type', fontsize=16)
            plt.tick_params(axis='both', which='major', labelsize=14)
            plt.grid(True, axis='y')

            plt.savefig(f'figures/new/bar_chart_mev_{mev_count}.png')
            plt.close()

if __name__ == "__main__":
    data_dir = 'data/vary_mev'
    mev_counts_to_plot = [1, 25, 50]
    inspect_columns(data_dir, mev_counts_to_plot)
    plot_bar_chart_for_mev(data_dir, mev_counts_to_plot)
