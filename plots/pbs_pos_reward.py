import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
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
        df['total_block_value'] = df['gas_captured'] + df['mev_captured']
        
        return df
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame()  # Return an empty DataFrame in case of error

# Function to process files in batches
def process_files_in_batches(files):
    dataframes = []
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
    return dataframes

# Function to calculate total profit
def calculate_total_profit(dataframes):
    if dataframes:
        all_data = pd.concat(dataframes, ignore_index=True)
        total_profit = all_data['total_block_value'].sum()
        return total_profit
    return 0

# Function to load data and calculate total profit
def load_and_calculate_profit(csv_path):
    all_files = glob.glob(os.path.join(csv_path, "*.csv"))
    dataframes = []
    batch_size = 50  # Adjust batch size based on memory constraints
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i + batch_size]
        dataframes.extend(process_files_in_batches(batch_files))
    total_profit = calculate_total_profit(dataframes)
    return total_profit

if __name__ == '__main__':
    csv_path_pos = "/Users/Tammy/Downloads/pos_vary_mev_and_characteristic"
    csv_path_pbs = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    
    total_profit_pos = load_and_calculate_profit(csv_path_pos)
    
    total_profit_pbs = load_and_calculate_profit(csv_path_pbs)
    
    profit_difference = total_profit_pbs - total_profit_pos
    
    # Check for zero total profit in PoS to avoid division by zero
    if total_profit_pos != 0:
        percentage_difference = (profit_difference / total_profit_pos) * 100
    else:
        percentage_difference = float('inf')

    print(f"Total Profit for PoS: {total_profit_pos}")
    print(f"Total Profit for PBS: {total_profit_pbs}")
    print(f"Profit Difference: {profit_difference}")
    if total_profit_pos != 0:
        print(f"Percentage Difference: {percentage_difference}%")
    else:
        print("Percentage Difference: Infinity (PoS profit is zero)")
    
    # Visualize the comparison
    labels = ['PoS', 'PBS']
    profits = [total_profit_pos, total_profit_pbs]
    
    plt.figure(figsize=(10, 6))
    plt.bar(labels, profits, color=['blue', 'orange'])
    plt.xlabel('System')
    plt.ylabel('Total Profit')
    plt.title('Total Profit Comparison between PoS and PBS')
    plt.show()
