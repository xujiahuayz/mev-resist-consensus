import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
import random

random.seed(16)

def plot_bid_dynamics(file_path, block_number):
    output_figure_path = 'figures/ss/bid_dynamics_selected_block.png'
    
    # Load data
    data = pd.read_csv(file_path)

    # Filter block-specific data and remove zero bids
    block_data = data[(data['block_num'] == block_number) & (data['bid'] > 0)]

    if block_data.empty:
        print(f"No valid bid data for Block {block_number}.")
        return

    # Convert columns to numeric if necessary
    block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
    block_data['round_num'] = pd.to_numeric(block_data['round_num'], errors='coerce')

    # Identify the winning builder
    last_round = block_data['round_num'].max()
    last_round_data = block_data[block_data['round_num'] == last_round]
    winning_builder = last_round_data.loc[last_round_data['bid'].idxmax()]['builder_id']

    # Select winning and 7 other builders
    selected_builders = block_data['builder_id'].unique()
    if len(selected_builders) > 8:
        selected_builders = np.random.choice(selected_builders, size=7, replace=False)
        selected_builders = np.append(selected_builders, winning_builder)

    # Plot
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
    bid_block_value_ratios = []
    bid_second_highest_block_value_ratios = []

    for block_number in data['block_num'].unique():
        block_data = data[data['block_num'] == block_number]

        # Convert columns to numeric if necessary
        block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
        block_data['block_value'] = pd.to_numeric(block_data['block_value'], errors='coerce')

        # Identify the winning builder and highest bid
        highest_bid_row = block_data.loc[block_data['bid'].idxmax()]
        highest_bid_id = highest_bid_row['builder_id']
        highest_bid = highest_bid_row['bid']

        # Identify the highest and second-highest block value
        sorted_block_values = block_data.sort_values(by='block_value', ascending=False)
        highest_block_value = sorted_block_values.iloc[0]['block_value']
        second_highest_block_value = sorted_block_values.iloc[1]['block_value'] if len(sorted_block_values) > 1 else 0

        # Check if highest bid builder also had the highest block value
        highest_block_value_id = sorted_block_values.iloc[0]['builder_id']
        if highest_bid_id == highest_block_value_id:
            match_count += 1

        # Calculate bid/block value percentage if block value is greater than zero
        if highest_block_value > 0:
            bid_block_value_ratio = (highest_bid / highest_block_value) * 100
            bid_block_value_ratios.append(bid_block_value_ratio)

        # Calculate bid/second-highest block value percentage if valid
        if second_highest_block_value > 0:
            bid_second_highest_block_value_ratio = (highest_bid / second_highest_block_value) * 100
            bid_second_highest_block_value_ratios.append(bid_second_highest_block_value_ratio)

    # Compute final statistics
    match_percentage = (match_count / total_blocks) * 100
    avg_bid_block_value_ratio = np.mean(bid_block_value_ratios) if bid_block_value_ratios else 0
    avg_bid_second_highest_block_value_ratio = np.mean(bid_second_highest_block_value_ratios) if bid_second_highest_block_value_ratios else 0

    return match_percentage, avg_bid_block_value_ratio, avg_bid_second_highest_block_value_ratio

def plot_block_value_dynamics(file_path, block_number):
    output_figure_path = 'figures/ss/block_value_dynamics_selected_block.png'
    
    # Load data
    data = pd.read_csv(file_path)

    # Filter only the selected block
    block_data = data[data['block_num'] == block_number]

    if block_data.empty:
        print(f"No valid block value data for Block {block_number}.")
        return

    # Convert columns to numeric if necessary
    block_data['block_value'] = pd.to_numeric(block_data['block_value'], errors='coerce')
    block_data['bid'] = pd.to_numeric(block_data['bid'], errors='coerce')
    block_data['round_num'] = pd.to_numeric(block_data['round_num'], errors='coerce')

    # Identify the winning builder by highest bid
    winning_builder = block_data.loc[block_data['bid'].idxmax()]['builder_id']

    # Select up to 8 builders randomly, ensuring the winning builder is included
    unique_builders = block_data['builder_id'].unique()
    
    if len(unique_builders) > 8:
        selected_builders = np.random.choice([b for b in unique_builders if b != winning_builder], size=7, replace=False)
        selected_builders = np.append(selected_builders, winning_builder)  # Ensure the winner is included
    else:
        selected_builders = unique_builders  # If fewer than 8 builders exist, show all

    # Plot block values for the selected builders
    plt.figure(figsize=(12, 8))
    for builder_id in selected_builders:
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
    block_number = 1

    # plot_bid_dynamics(file_path, block_number)
    plot_block_value_dynamics(file_path, block_number)

    match_percentage, avg_bid_block_value_ratio, avg_bid_second_highest_block_value_ratio = analyze_data(file_path)
    print(f"The winning bid has the highest block value {match_percentage:.2f}% of the time.")
    print(f"On average, the winning bid is {avg_bid_block_value_ratio:.2f}% of the highest block value.")
    print(f"On average, the winning bid is {avg_bid_second_highest_block_value_ratio:.2f}% of the second-highest block value.")
