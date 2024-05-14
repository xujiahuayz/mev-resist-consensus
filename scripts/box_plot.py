import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, as_completed

# Function to read and process a single file
def process_file(file):
    try:
        # Extract parameters from the filename
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))
        
        df = pd.read_csv(file)
        
        # Add the parameters to the DataFrame
        df['mev_builders'] = mev_builders
        df['characteristic'] = characteristic
        df['total_block_value'] = df['gas_captured'] + df['mev_captured']
        
        return df
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame()

# Function to process files in batches
def process_files_in_batches(files, dataframes):
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_file, file): file for file in files}
        for future in as_completed(futures):
            file = futures[future]
            try:
                result = future.result()
                if not result.empty:
                    dataframes.append(result)
            except Exception as e:
                print(f"Error with file {file}: {e}")

# Function to create and save the violin plot for reward distribution
def plot_reward_distribution(data, save_dir):
    # Calculate the reward for each block
    data['reward'] = data['gas_captured'] + data['mev_captured'] - data['block_bid']
    
    # Apply log transformation to the reward to reduce skewness
    data['log_reward'] = np.log1p(data['reward'])
    
    # Create a DataFrame for plotting
    reward_data = pd.DataFrame({
        'Log Reward': data['log_reward'],
        'Builder Type': np.where(data['builder_type'] == 1, 'Non-MEV', 'MEV')
    })
    
    # Plot violin plots with Seaborn's pastel palette
    plt.figure(figsize=(10, 8))
    sns.set(style="whitegrid")
    sns.violinplot(x='Builder Type', y='Log Reward', data=reward_data, palette='pastel')
    plt.title('Distribution of Log-Transformed Rewards between MEV and Non-MEV Builders')
    plt.xlabel('Builder Type')
    plt.ylabel('Log Reward')
    plt.savefig(os.path.join(save_dir, 'reward_distribution_violinplot.png'), bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.close()

if __name__ == '__main__':
    # Define the path to the folder containing the CSV files
    csv_path = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"  # Save plots in a directory named "figures" within the repository
    
    # Create directory for saving plots if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Use glob to get all CSV file paths in the specified directory
    all_files = glob.glob(os.path.join(csv_path, "*.csv"))
    
    # Initialize an empty list to collect DataFrames
    dataframes = []
    
    # Split the files into batches to manage memory usage better
    batch_size = 50  # Adjust batch size based on memory constraints
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i + batch_size]
        process_files_in_batches(batch_files, dataframes)
    
    # Concatenate all DataFrames into one
    if dataframes:
        all_data = pd.concat(dataframes, ignore_index=True)
    
        # Group by 'mev_builders' and 'characteristic' and calculate mean values
        grouped_data = all_data.groupby(['mev_builders', 'characteristic']).mean().reset_index()
           
        # Generate and save the violin plot for reward distribution
        plot_reward_distribution(all_data, save_dir)
    else:
        print("No data to plot.")
