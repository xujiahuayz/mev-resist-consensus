import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to read and process a single file
def process_file(file):
    try:
        # Extract parameters from the filename
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))  # Correct extraction of characteristic
        
        # Read the CSV file
        df = pd.read_csv(file)
        
        # Add the parameters to the DataFrame
        df['mev_builders'] = mev_builders
        df['characteristic'] = characteristic
        df['total_block_value'] = df['gas_captured'] + df['mev_captured']
        
        return df
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

# Function to load data and classify blocks as MEV or non-MEV
def load_and_classify_blocks(csv_path):
    all_files = glob.glob(os.path.join(csv_path, "*.csv"))
    mev_blocks = 0
    non_mev_blocks = 0
    for file in all_files:
        df = process_file(file)
        if not df.empty:
            mev_blocks += (df['mev_captured'] > 0).sum()
            non_mev_blocks += (df['mev_captured'] == 0).sum()
    return mev_blocks, non_mev_blocks

# Function to create bar plots for MEV and non-MEV blocks
def create_block_plots(pos_mev_blocks, pos_non_mev_blocks, pbs_mev_blocks, pbs_non_mev_blocks, save_path):
    labels = ['PoS', 'PBS']
    mev_blocks = [pos_mev_blocks, pbs_mev_blocks]
    non_mev_blocks = [pos_non_mev_blocks, pbs_non_mev_blocks]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bar_width = 0.35
    index = np.arange(len(labels))
    
    bar1 = ax.bar(index, mev_blocks, bar_width, label='MEV Blocks', color=sns.color_palette("pastel")[0])
    bar2 = ax.bar(index + bar_width, non_mev_blocks, bar_width, label='Non-MEV Blocks', color=sns.color_palette("pastel")[1])
    
    ax.set_xlabel('System', fontsize=20)
    ax.set_ylabel('Number of Blocks', fontsize=20)
    ax.set_xticks(index + bar_width / 2)
    ax.set_xticklabels(labels, fontsize=16)
    ax.legend(loc='best', fontsize=12)
    
    fig.tight_layout()
    
    # Save the figure
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()

if __name__ == '__main__':
    csv_path_pos = "/Users/Tammy/Downloads/pos_vary_mev_and_characteristic"
    csv_path_pbs = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"
    save_path = os.path.join(save_dir, 'mev_vs_non_mev_blocks.png')
    
    pos_mev_blocks, pos_non_mev_blocks = load_and_classify_blocks(csv_path_pos)
    pbs_mev_blocks, pbs_non_mev_blocks = load_and_classify_blocks(csv_path_pbs)
    
    create_block_plots(pos_mev_blocks, pos_non_mev_blocks, pbs_mev_blocks, pbs_non_mev_blocks, save_path)
