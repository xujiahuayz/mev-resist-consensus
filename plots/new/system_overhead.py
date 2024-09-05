import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d
import os

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

def interpolate_and_smooth(x, y, num_points=50, window_length=7, polyorder=2):
    """Smooth data using interpolation and the Savitzky-Golay filter."""
    # Interpolate the data to increase resolution
    interp_func = interp1d(x, y, kind='linear', fill_value="extrapolate")
    x_new = np.linspace(min(x), max(x), num_points)
    y_new = interp_func(x_new)

    # Apply the Savitzky-Golay filter to smooth the interpolated data
    y_smooth = savgol_filter(y_new, window_length, polyorder)

    # Round the smoothed data to two significant figures
    y_smooth = np.round(y_smooth, 2)

    return x_new, y_smooth

def plot_total_profits(avg_profits, output_file):
    """Plots the total profits of PBS and PoS systems."""
    plt.figure(figsize=(10, 6))

    # Prepare data for plotting
    mev_counts = list(avg_profits['pbs'].keys())
    avg_profit_pbs = [avg_profits['pbs'][mc] for mc in mev_counts]
    avg_profit_pos = [avg_profits['pos'][mc] for mc in mev_counts]

    # Smooth data
    x_pbs, smoothed_pbs = interpolate_and_smooth(mev_counts, avg_profit_pbs, window_length=7, polyorder=2)
    x_pos, smoothed_pos = interpolate_and_smooth(mev_counts, avg_profit_pos, window_length=7, polyorder=2)

    # Plotting
    plt.plot(x_pbs, smoothed_pbs, label='PBS', color='blue')
    plt.plot(x_pos, smoothed_pos, label='PoS', color='orange')

    # Labels and Title
    plt.xlabel('Number of MEV Builders/Validators', fontsize=20)
    plt.ylabel('Total System Profit', fontsize=20)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    plt.legend(fontsize=18)
    plt.grid(axis='y')

    # Save the plot
    plt.savefig(output_file)
    plt.close()

if __name__ == "__main__":
    data_dir = 'data/100_runs'
    check_data_files(data_dir, MEV_BUILDER_COUNTS)
    total_profits = load_transaction_data(data_dir, MEV_BUILDER_COUNTS)
    avg_profits = calculate_average_profits(total_profits)
    plot_total_profits(avg_profits, 'figures/new/total_profit_comparison.png')
