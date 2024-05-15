import pandas as pd
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Function to calculate the Gini coefficient
def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    array = array.flatten().astype(float)  # Ensure the array is of float type
    if np.amin(array) < 0:
        array -= np.amin(array)  # values cannot be negative
    array += 0.0000001  # values cannot be 0
    array = np.sort(array)  # values must be sorted
    index = np.arange(1, array.shape[0] + 1)  # index per array element
    n = array.shape[0]  # number of array elements
    return ((np.sum((2 * index - n - 1) * array)) / (n * np.sum(array)))  # Gini coefficient

# Function to read and process a single file
def process_file(file, is_pos=True):
    try:
        df = pd.read_csv(file)
        
        # Add the parameters to the DataFrame
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_entity = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))
        
        df['mev_entity'] = mev_entity
        df['characteristic'] = characteristic
        df['reward'] = df['gas_captured'] + df['mev_captured']
        return df, mev_entity, characteristic
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame(), None, None

# Function to plot the heat maps of Gini coefficients for PoS and PBS
def plot_heatmap(data, title, save_path):
    # Pivot the data for heat map plotting
    pivot = data.pivot("MEV Entity", "Characteristic", "Gini Coefficient")

    # Create the heat map
    plt.figure(figsize=(10, 8))
    sns.heatmap(pivot, cmap="YlGnBu", cbar_kws={'label': 'Gini Coefficient'}, annot=False)
    plt.title(title)
    plt.xlabel('Characteristic')
    plt.ylabel('MEV Entity')

    # Save the figure
    plt.tight_layout()
    plt.savefig(save_path, bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.show()
    plt.close()

if __name__ == '__main__':
    # Define the paths to the folders containing the CSV files
    pos_csv_path = "/Users/Tammy/Downloads/pos_vary_mev_and_characteristic"
    pbs_csv_path = "/Users/Tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures"  
    
    # Create directory for saving plots if it doesn't exist
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    # List the available CSV files in the directories
    pos_files = os.listdir(pos_csv_path)
    pbs_files = os.listdir(pbs_csv_path)
    
    # Process and collect Gini coefficients for PoS
    pos_gini_data = []
    for file_name in pos_files:
        file_path = os.path.join(pos_csv_path, file_name)
        df, mev_validators, characteristic = process_file(file_path, is_pos=True)
        if df is not None and not df.empty:
            gini_coeff = gini(df['reward'].values)
            pos_gini_data.append((mev_validators, characteristic, gini_coeff))
        else:
            print(f"No data to plot for {file_name}.")

    # Process and collect Gini coefficients for PBS
    pbs_gini_data = []
    for file_name in pbs_files:
        file_path = os.path.join(pbs_csv_path, file_name)
        df, mev_builders, characteristic = process_file(file_path, is_pos=False)
        if df is not None and not df.empty:
            gini_coeff = gini(df['reward'].values)
            pbs_gini_data.append((mev_builders, characteristic, gini_coeff))
        else:
            print(f"No data to plot for {file_name}.")

    # Convert the Gini data to DataFrames
    pos_gini_df = pd.DataFrame(pos_gini_data, columns=['MEV Entity', 'Characteristic', 'Gini Coefficient'])
    pbs_gini_df = pd.DataFrame(pbs_gini_data, columns=['MEV Entity', 'Characteristic', 'Gini Coefficient'])

    # Plot the heat maps of Gini coefficients for PoS and PBS
    plot_heatmap(pos_gini_df, 'Gini Coefficient for PoS', os.path.join(save_dir, 'gini_coefficient_heatmap_pos.png'))
    plot_heatmap(pbs_gini_df, 'Gini Coefficient for PBS', os.path.join(save_dir, 'gini_coefficient_heatmap_pbs.png'))
