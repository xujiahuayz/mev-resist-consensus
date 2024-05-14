import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from concurrent.futures import ProcessPoolExecutor, as_completed

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
        
        return df
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

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

if __name__ == '__main__':
    # Define the path to the folder containing the CSV files
    csv_path = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    
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
    
        # Group by 'mev_builders' and 'characteristic' and calculate mean gas_captured and mev_captured
        grouped_data = all_data.groupby(['mev_builders', 'characteristic']).mean().reset_index()
    
        # Pivot the data to create a grid for plotting
        pivot_table = grouped_data.pivot('mev_builders', 'characteristic', 'mev_captured')
        
        # Create a meshgrid for plotting
        x = pivot_table.index.values
        y = pivot_table.columns.values
        x, y = np.meshgrid(x, y)
        z = pivot_table.values.T  # Transpose to match the shape
    
        # Create a 3D plot using Matplotlib
        fig = plt.figure(figsize=(10, 8))
        ax = fig.add_subplot(111, projection='3d')
    
        # Plotting the surface
        surf = ax.plot_surface(x, y, z, cmap='viridis')
    
        # Remove the redundant color bar
        # color_bar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=5)
        # color_bar.set_label('MEV Captured')
    
        ax.set_xlabel('MEV Builders')
        ax.set_ylabel('Characteristic')
        ax.set_zlabel('MEV Captured')
    
        plt.show()
    else:
        print("No data to plot.")
