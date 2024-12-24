import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# File paths
file_path = 'data/same_seed/bid_builder20.csv'  # Path to the CSV file
output_figure_path = 'figures/ss/bid_dynamics.png'  # Path to save the figure

# Load the data into a DataFrame
data = pd.read_csv(file_path)

# Extract the last block's data
last_block = data['block_num'].max()
last_block_data = data[data['block_num'] == last_block]

# Prepare the data for plotting
last_block_data['bid_value'] = last_block_data['bid_value'].str.strip('[]').str.split(',')
last_block_data = last_block_data.explode('bid_value')
last_block_data['bid_value'] = last_block_data['bid_value'].astype(float)
last_block_data['bid_round'] = last_block_data['bid_round'].astype(int)

# Plotting with Seaborn
plt.figure(figsize=(12, 8))
sns.lineplot(
    data=last_block_data,
    x='bid_round',
    y='bid_value',
    hue='builder_id',
    marker='o',
    palette='tab20',
    linewidth=2
)

# Add titles and labels
plt.title(f'Bid Dynamics for Block {last_block}', fontsize=16)
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
