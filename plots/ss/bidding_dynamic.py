import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# File paths
file_path = 'data/same_seed/bid_builder20.csv'  # Path to the CSV file
output_figure_path = 'figures/ss/bid_dynamics_first_block.png'  # Path to save the figure

# Load the data into a DataFrame
data = pd.read_csv(file_path)

# Extract the first block's data
first_block = data['block_num'].min()
first_block_data = data[data['block_num'] == first_block]

# Ensure 'bid_value' column is treated as a string, then clean and split
first_block_data['bid_value'] = first_block_data['bid_value'].astype(str).str.strip('[]').str.split(',')

# Explode the list of bid values into separate rows
first_block_data = first_block_data.explode('bid_value')

# Convert bid_value and bid_round to numeric types
first_block_data['bid_value'] = pd.to_numeric(first_block_data['bid_value'], errors='coerce')
first_block_data['bid_round'] = pd.to_numeric(first_block_data['bid_round'], errors='coerce')

# Plotting with Seaborn
plt.figure(figsize=(12, 8))
sns.lineplot(
    data=first_block_data,
    x='bid_round',
    y='bid_value',
    hue='builder_id',
    marker='o',
    palette='tab20',
    linewidth=2
)

# Add titles and labels
plt.title(f'Bid Dynamics for Block {first_block}', fontsize=16)
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
