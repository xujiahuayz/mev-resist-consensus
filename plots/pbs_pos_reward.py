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

# Function to load data and calculate total reward for all files in a directory
def load_and_calculate_total_reward(csv_path):
    all_files = glob.glob(os.path.join(csv_path, "*.csv"))
    dataframes = []
    for file in all_files:
        df = process_file(file)
        if not df.empty:
            dataframes.append(df)
    return dataframes

# Function to compute the total reward differences
def compute_reward_differences(pos_data, pbs_data):
    differences = []
    for pos_df, pbs_df in zip(pos_data, pbs_data):
        pos_total_reward = pos_df['total_block_value'].sum()
        pbs_total_reward = pbs_df['total_block_value'].sum()
        differences.append(pbs_total_reward - pos_total_reward)
    return differences

# Function to create a heatmap
def create_heatmap(differences, labels):
    data_matrix = np.array(differences).reshape(len(set(labels[0])), len(set(labels[1])))
    plt.figure(figsize=(12, 8))
    sns.heatmap(data_matrix, annot=False, cmap="YlGnBu", xticklabels=sorted(set(labels[1])), yticklabels=sorted(set(labels[0])))
    plt.xlabel('Characteristic', fontsize=16)
    plt.ylabel('MEV Builders', fontsize=16)
    plt.tick_params(axis='both', which='major', labelsize=12)
    
    # Custom y-tick labels to show every 5 MEV Builders
    y_ticks = plt.gca().get_yticks()
    y_labels = [int(label) if idx % 5 == 0 else '' for idx, label in enumerate(y_ticks)]
    plt.gca().set_yticklabels(y_labels)
    
    # Save the figure as 'total_reward_difference_heatmap.png'
    plt.savefig('total_reward_difference_heatmap.png', bbox_inches='tight')
    plt.show()

if __name__ == '__main__':
    csv_path_pos = "/Users/Tammy/Downloads/pos_vary_mev_and_characteristic"
    csv_path_pbs = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    
    pos_data = load_and_calculate_total_reward(csv_path_pos)
    pbs_data = load_and_calculate_total_reward(csv_path_pbs)
    
    if len(pos_data) != len(pbs_data):
        print("Mismatch in the number of files between PoS and PBS directories.")
    else:
        reward_differences = compute_reward_differences(pos_data, pbs_data)
        
        # Extract parameters for labeling the heatmap axes
        mev_builders = [df['mev_builders'].iloc[0] for df in pos_data]
        characteristics = [df['characteristic'].iloc[0] for df in pos_data]
        
        create_heatmap(reward_differences, (mev_builders, characteristics))
