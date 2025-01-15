import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

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
    winning_builder = last_round_data.loc[last_round_data['bid'].idxmax()]

    # Plotting with Seaborn
    plt.figure(figsize=(12, 8))
    for builder_id, builder_data in block_data.groupby('builder_id'):
        # Determine the color and label
        is_winner = builder_id == winning_builder['builder_id']
        color = 'red' if is_winner else None
        strategy_label = builder_data['strategy'].iloc[0] + (" (win)" if is_winner else "")
        
        sns.lineplot(
            data=builder_data,
            x='round_num',
            y='bid',
            label=strategy_label,
            color=color,
            marker='o',
            linewidth=1  # Thinner lines
        )

    # Add titles and labels
    plt.title(f'Bid Dynamics for Block {block_number}', fontsize=16)
    plt.xlabel('Bidding Round', fontsize=14)
    plt.ylabel('Bid Value', fontsize=14)
    plt.legend(title='Strategy', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_figure_path), exist_ok=True)

    # Save the plot
    plt.savefig(output_figure_path)

    # Show the plot
    plt.show()

# Example Usage
file_path = 'data/same_seed/bid_builder20.csv'  # Path to the CSV file
output_figure_path = 'figures/ss/bid_dynamics_selected_block.png'  # Path to save the figure
block_number = 10  # Specify the block number you want to visualize
plot_bid_dynamics(file_path, output_figure_path, block_number)
