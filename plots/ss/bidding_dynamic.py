import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

def plot_bid_dynamics(file_path, output_figure_path, block_number):
    # Load the data into a DataFrame
    data = pd.read_csv(file_path)

    # Extract the specified block's data
    block_data = data[data['block_num'] == block_number]

    # Ensure 'bid_value' column is treated as a string, then clean and split
    block_data['bid_value'] = block_data['bid_value'].astype(str).str.strip('[]').str.split(',')

    # Explode the list of bid values into separate rows
    block_data = block_data.explode('bid_value')

    # Convert bid_value and bid_round to numeric types
    block_data['bid_value'] = pd.to_numeric(block_data['bid_value'], errors='coerce')
    block_data['bid_round'] = pd.to_numeric(block_data['bid_round'], errors='coerce')

    # Plotting with Seaborn
    plt.figure(figsize=(12, 8))
    sns.lineplot(
        data=block_data,
        x='bid_round',
        y='bid_value',
        hue='builder_id',
        marker='o',
        palette='tab20',
        linewidth=2
    )

    # Add titles and labels
    plt.title(f'Bid Dynamics for Block {block_number}', fontsize=16)
    plt.xlabel('Bidding Round', fontsize=14)
    plt.ylabel('Bid Value', fontsize=14)
    plt.legend(title='Builder ID', bbox_to_anchor=(1.05, 1), loc='upper left')
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
block_number = 3  # Specify the block number you want to visualize
plot_bid_dynamics(file_path, output_figure_path, block_number)
