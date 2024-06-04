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
        return pd.DataFrame()

def load_and_calculate_total_reward(csv_path):
    all_files = glob.glob(os.path.join(csv_path, "*.csv"))
    dataframes = []
    for file in all_files:
        df = process_file(file)
        if not df.empty:
            dataframes.append(df)
    return dataframes

def compute_means(dataframes, interval=50):
    gas_means = []
    mev_means = []
    for i in range(0, len(dataframes), interval):
        subset = pd.concat(dataframes[i:i + interval])
        mean_gas = subset['gas_captured'].mean()
        mean_mev = subset['mev_captured'].mean()
        gas_means.append(mean_gas)
        mev_means.append(mean_mev)
    return gas_means, mev_means

# Function to create bar plots using seaborn
def create_bar_plots(pos_gas_means, pos_mev_means, pbs_gas_means, pbs_mev_means, save_path):
    labels = [f'{10*i+1}-{10*(i+1)}' for i in range(len(pos_gas_means))]
    
    pos_data = pd.DataFrame({
        'Batch': labels,
        'Gas': pos_gas_means,
        'MEV': pos_mev_means,
        'Type': 'PoS Gas'
    })
    
    pbs_data = pd.DataFrame({
        'Batch': labels,
        'Gas': pbs_gas_means,
        'MEV': pbs_mev_means,
        'Type': 'PBS Gas'
    })
    
    data = pd.concat([pos_data, pbs_data])
    
    pastel_colors = sns.color_palette("pastel")
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot gas
    sns.barplot(data=data, x='Batch', y='Gas', hue='Type', ax=ax, palette=pastel_colors[:2])
    
    # Plot MEV on top of gas
    for i in range(len(labels)):
        ax.bar(i - 0.2, pos_mev_means[i], width=0.4, bottom=pos_gas_means[i], color=pastel_colors[2], label='PoS MEV' if i == 0 else "")
        ax.bar(i + 0.2, pbs_mev_means[i], width=0.4, bottom=pbs_gas_means[i], color=pastel_colors[3], label='PBS MEV' if i == 0 else "")
    
    ax.set_xlabel('MEV Builders Range', fontsize=16)
    ax.set_ylabel('Mean Reward', fontsize=16)
    ax.set_xticklabels(labels, rotation=45, fontsize=12)
    ax.legend(loc='upper right', fontsize=12)

    fig.tight_layout()
    
    # Save the figure
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()

if __name__ == '__main__':
    csv_path_pos = "/Users/Tammy/Downloads/pos_vary_mev_and_characteristic"
    csv_path_pbs = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"
    save_path = os.path.join(save_dir, 'reward_comparison_bar_plot.png')
    
    pos_data = load_and_calculate_total_reward(csv_path_pos)
    pbs_data = load_and_calculate_total_reward(csv_path_pbs)
    
    if len(pos_data) != len(pbs_data):
        print("Mismatch in the number of files between PoS and PBS directories.")
    else:
        pos_gas_means, pos_mev_means = compute_means(pos_data, interval=50)
        pbs_gas_means, pbs_mev_means = compute_means(pbs_data, interval=50)
        
        create_bar_plots(pos_gas_means, pos_mev_means, pbs_gas_means, pbs_mev_means, save_path)