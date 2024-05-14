import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to read and process a single file
def process_file(file):
    try:
        df = pd.read_csv(file)
        
        # Add the parameters to the DataFrame
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))
        
        df['mev_builders'] = mev_builders
        df['characteristic'] = characteristic
        df['total_block_value'] = df['gas_captured'] + df['mev_captured']
        df['reward'] = df['gas_captured'] + df['mev_captured'] - df['block_bid']
        
        return df
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame()

# Function to create and save the violin plot for reward distribution
def plot_reward_distribution(data, file_name, save_dir):
    # Apply log transformation to the reward to reduce skewness
    data['log_reward'] = np.log1p(data['reward'])
    
    # Create a DataFrame for plotting
    reward_data = pd.DataFrame({
        'Log Reward': data['log_reward'],
        'Builder Type': np.where(data['builder_type'] == 1, 'Non-MEV', 'MEV')
    })
    
    # Plot violin plots with Seaborn's pastel palette
    plt.figure(figsize=(12, 8))
    sns.set(style="whitegrid")
    sns.violinplot(x='Builder Type', y='Log Reward', data=reward_data, palette='pastel')
    plt.title(f'Distribution of Log-Transformed Rewards: {file_name}')
    plt.xlabel('Builder Type')
    plt.ylabel('Log Reward')
    plt.savefig(os.path.join(save_dir, f'reward_distribution_violinplot_{file_name}.png'), bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.close()

if __name__ == '__main__':
    # Define the path to the folder containing the CSV files
    csv_path = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"  # Save plots in a directory named "figures" within the repository
    
    # Create directory for saving plots if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # Specify the representative CSV files
    representative_files = [
        "mev_builders=1characteristic=0.2.csv",
        "mev_builders=1characteristic=0.6.csv",
        "mev_builders=1characteristic=1.csv",
        "mev_builders=25characteristic=0.2.csv",
        "mev_builders=25characteristic=0.6.csv",
        "mev_builders=25characteristic=1.csv",
        "mev_builders=49characteristic=0.2.csv",
        "mev_builders=49characteristic=0.6.csv",
        "mev_builders=49characteristic=1.csv"
    ]
    
    # Process and plot each file separately
    for file_name in representative_files:
        file_path = os.path.join(csv_path, file_name)
        df = process_file(file_path)
        if not df.empty:
            plot_reward_distribution(df, file_name, save_dir)
        else:
            print(f"No data to plot for {file_name}.")
