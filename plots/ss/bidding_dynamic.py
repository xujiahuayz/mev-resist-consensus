import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np

def plot_bid_dynamics(file_path, output_figure_path, block_number):
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
            linewidth=1,  # Thinner line
            color='red' if is_winner else 'grey',
            markersize=4  # Smaller marker size
        )
        # Annotate the winning line
        if is_winner:
            last_point = builder_data.iloc[-1]
            plt.text(last_point['round_num'], last_point['bid'], 'Win', color='red')

    # Add titles and labels
    plt.xlabel('Bidding Round', fontsize=20)
    plt.ylabel('Bid Value', fontsize=20)
    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_figure_path), exist_ok=True)

    # Save the plot
    plt.savefig(output_figure_path)

    # Show the plot
    plt.show()

# Example usage
file_path = 'data/same_seed/bid_builder20.csv'
output_figure_path = 'figures/ss/bid_dynamics_selected_block.png'
block_number = 5
plot_bid_dynamics(file_path, output_figure_path, block_number)
