import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from scipy.signal import savgol_filter

# Constants
MEV_BUILDER_COUNTS = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

def check_data_files(data_dir, mev_counts):
    """Check if the expected files exist and print their paths."""
    for mev_count in mev_counts:
        for run_id in range(1, 11):
            # Construct file paths for PBS and PoS
            pbs_file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'pbs', 'block_data_pbs.csv')
            pos_file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'pos', 'block_data_pos.csv')

def load_transaction_data(data_dir, mev_counts):
    """Loads transaction data for both PBS and PoS systems."""
    total_profits = {'pbs': {}, 'pos': {}}

    for mev_count in mev_counts:
        total_profits['pbs'][mev_count] = []
        total_profits['pos'][mev_count] = []

        for run_id in range(1, 11):
            # Load PBS transactions
            pbs_file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'pbs', 'block_data_pbs.csv')
            if os.path.exists(pbs_file_path):
                df_pbs = pd.read_csv(pbs_file_path)

                # Calculate total profit for PBS
                pbs_total_gas_fee = df_pbs['total_gas'].sum()
                pbs_total_mev_captured = df_pbs['total_mev_captured'].sum()
                total_profits['pbs'][mev_count].append(pbs_total_gas_fee + pbs_total_mev_captured)

            # Load PoS transactions
            pos_file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', 'pos', 'block_data_pos.csv')
            if os.path.exists(pos_file_path):
                df_pos = pd.read_csv(pos_file_path)

                # Calculate total profit for PoS
                pos_total_gas_fee = df_pos['total_gas'].sum()
                pos_total_mev_captured = df_pos['total_mev_captured'].sum()
                total_profits['pos'][mev_count].append(pos_total_gas_fee + pos_total_mev_captured)
 
    return total_profits

def calculate_average_profits(total_profits):
    """Calculates the average total profit for each MEV builder/validator count."""
    avg_profits = {'pbs': {}, 'pos': {}}

    for system in ['pbs', 'pos']:
        for mev_count in MEV_BUILDER_COUNTS:
            profits = total_profits[system][mev_count]
            if profits:
                avg_profits[system][mev_count] = np.mean(profits)
            else:
                avg_profits[system][mev_count] = np.nan
    return avg_profits

def smooth_data(y, window_length=7, polyorder=2):
    """Smooth data using the Savitzky-Golay filter."""
    # Ensure window length is odd and appropriate for data size
    if len(y) < window_length:
        return y  # Return original data if too short to smooth
    if window_length % 2 == 0:
        window_length += 1  # Make window length odd
    return savgol_filter(y, window_length, polyorder)

def plot_total_profits(avg_profits, output_file):
    """Plots the total profits of PBS and PoS systems."""
    plt.figure(figsize=(10, 6))

    # Prepare data for plotting
    mev_counts = list(avg_profits['pbs'].keys())
    avg_profit_pbs = [avg_profits['pbs'][mc] for mc in mev_counts]
    avg_profit_pos = [avg_profits['pos'][mc] for mc in mev_counts]

    # Smooth data
    smoothed_pbs = smooth_data(avg_profit_pbs, window_length=7, polyorder=2)
    smoothed_pos = smooth_data(avg_profit_pos, window_length=7, polyorder=2)

    # Plotting
    plt.plot(mev_counts, smoothed_pos, label='PBS', color='blue')
    plt.plot(mev_counts, smoothed_pbs, label='PoS', color='orange')

    # Labels and Title
    plt.xlabel('Number of MEV Builders/Validators')
    plt.ylabel('Average Total Profit')
    plt.title('Average Total Profit of PBS and PoS Systems')
    plt.legend()
    plt.grid(True)

    # Save the plot
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    check_data_files(data_dir, MEV_BUILDER_COUNTS)
    total_profits = load_transaction_data(data_dir, MEV_BUILDER_COUNTS)
    avg_profits = calculate_average_profits(total_profits)
    plot_total_profits(avg_profits, 'figures/total_profit_comparison.png')
