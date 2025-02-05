import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import random

# random.seed(16)

def plot_bid_dynamics(file_path, block_number):
    # Define the output file path within the function
    output_figure_path = 'figures/ss/bid_dynamics_selected_block.png'

    # Load the data into a DataFrame
    data = pd.read_csv(file_path)

    # Extract the specified block's data
    block_data = data[data['block_num'] == block_number]

    # Convert columns to numeric if necessary
    block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
    block_data['round_num'] = pd.to_numeric(block_data['round_num'], errors='coerce')

    # Identify the winning builder (highest bid at the last round for the block)
    last_round = block_data['round_num'].max()
    last_round_data = block_data[block_data['round_num'] == last_round]
    winning_builder = last_round_data.loc[last_round_data['bid'].idxmax()]['builder_id']

    # Filter data to include only winning and 7 other representative lines
    selected_builders = block_data['builder_id'].unique()
    if len(selected_builders) > 8:
        selected_builders = np.random.choice(selected_builders, size=7, replace=False)
        selected_builders = np.append(selected_builders, winning_builder)

    # Plotting
    plt.figure(figsize=(12, 8))
    for builder_id in selected_builders:
        builder_data = block_data[block_data['builder_id'] == builder_id]
        is_winner = builder_id == winning_builder
        sns.lineplot(
            data=builder_data,
            x='round_num',
            y='bid',
            marker='o',
            linewidth=1,
            color='red' if is_winner else 'grey',
            markersize=4
        )
        if is_winner:
            last_point = builder_data.iloc[-1]
            plt.text(last_point['round_num'], last_point['bid'], 'Win', color='red')

    plt.xlabel('Bidding Round', fontsize=20)
    plt.ylabel('Bid Value', fontsize=20)
    plt.tick_params(axis='both', which='major', labelsize=18)
    plt.tight_layout()
    plt.savefig(output_figure_path)
    plt.show()

def analyze_data(file_path):
    data = pd.read_csv(file_path)
    total_blocks = data['block_num'].nunique()
    match_count = 0

    for block_number in data['block_num'].unique():
        block_data = data[data['block_num'] == block_number]

        # Convert columns to numeric if necessary
        block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
        block_data['block_value'] = pd.to_numeric(block_data['block_value'], errors='coerce')

        # Identify the winning builder and highest block value builder
        highest_bid_id = block_data.loc[block_data['bid'].idxmax()]['builder_id']
        highest_block_value_id = block_data.loc[block_data['block_value'].idxmax()]['builder_id']

        if highest_bid_id == highest_block_value_id:
            match_count += 1

    # Calculate the percentage of matches
    match_percentage = (match_count / total_blocks) * 100
    return match_percentage

def plot_block_value_dynamics(file_path, block_number):
    output_figure_path = 'figures/ss/block_value_dynamics_selected_block.png'
    data = pd.read_csv(file_path)
    block_data = data[data['block_num'] == block_number]
    block_data['block_value'] = pd.to_numeric(block_data['block_value'], errors='coerce')
    block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
    block_data['round_num'] = pd.to_numeric(block_data['round_num'], errors='coerce')

    # Winning builder by bid, not block value
    winning_builder = block_data.loc[block_data['bid'].idxmax()]['builder_id']

    plt.figure(figsize=(12, 8))
    for builder_id in block_data['builder_id'].unique():
        builder_data = block_data[block_data['builder_id'] == builder_id]
        is_winner = builder_id == winning_builder
        sns.lineplot(
            data=builder_data,
            x='round_num',
            y='block_value',
            marker='o',
            linewidth=1,
            color='red' if is_winner else 'grey',
            markersize=4
        )
        if is_winner:
            last_point = builder_data.iloc[-1]
            plt.text(last_point['round_num'], last_point['block_value'], 'Win', color='red')

    plt.xlabel('Bidding Round', fontsize=20)
    plt.ylabel('Block Value', fontsize=20)
    plt.tick_params(axis='both', which='major', labelsize=18)
    plt.tight_layout()
    plt.savefig(output_figure_path)
    plt.show()

if __name__ == "__main__":
    file_path = 'data/same_seed/bid_builder10.csv'
    block_number = 2
    plot_bid_dynamics(file_path, block_number)
    plot_block_value_dynamics(file_path, block_number)
    match_percentage = analyze_data(file_path)
    print(f"The winning bid has the highest block value {match_percentage:.2f}% of the time.")

