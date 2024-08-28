import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D
from scipy.interpolate import griddata

sns.set_theme(style="whitegrid")

# Load the transaction data and compute the average CDF of profits
def compute_cdf_profit(data_dir, mev_counts, system):
    cdf_data = []
    for mev_count in mev_counts:
        all_profits = []
        for run_id in range(1, 51):  # Assuming 50 runs
            file_path = os.path.join(data_dir, f'run{run_id}', f'mev{mev_count}', system, f'transaction_data_{system}.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                df['profit'] = np.log(df['mev_captured'] + 1)  # Log of profit (to avoid log(0))
                all_profits.extend(df['profit'].values)
        
        if all_profits:
            sorted_profits = np.sort(all_profits)
            cdf = np.arange(1, len(sorted_profits) + 1) / len(sorted_profits)  # Compute CDF
            cdf_data.append((mev_count, sorted_profits, cdf))

    return cdf_data

def plot_smooth_3d_surface(data_dir, mev_counts, system, output_file):
    cdf_data = compute_cdf_profit(data_dir, mev_counts, system)

    # Seaborn settings
    sns.set(style="whitegrid")

    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111, projection='3d')

    # Prepare data for surface plot
    all_x = []
    all_y = []
    all_z = []
    
    for mev_count, profits, cdf in cdf_data:
        all_x.extend([mev_count] * len(profits))
        all_y.extend(cdf)
        all_z.extend(profits)

    all_x = np.array(all_x)
    all_y = np.array(all_y)
    all_z = np.array(all_z)

    # Create grid for the smooth surface
    grid_x, grid_y = np.meshgrid(
        np.linspace(min(mev_counts), max(mev_counts), 100),
        np.linspace(0, 1, 100)
    )
    grid_z = griddata((all_x, all_y), all_z, (grid_x, grid_y), method='cubic')

    # Plot the surface
    ax.plot_surface(grid_x, grid_y, grid_z, cmap='viridis', alpha=0.8)

    ax.set_xlabel('Number of MEV Builders/Validators', fontsize=12)
    ax.set_ylabel('CDF of Profit', fontsize=12)
    ax.set_zlabel('Log of Profit', fontsize=12)
    ax.set_title(f'Smooth 3D Plot of {system.upper()} Profits', fontsize=15)

    plt.savefig(output_file)
    plt.show()

if __name__ == "__main__":
    mev_counts = [0, 1, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]  # Example MEV builder/validator counts
    data_dir_pbs = 'data/100_runs'  # Path to PBS data
    data_dir_pos = 'data/100_runs'  # Path to POS data

    plot_smooth_3d_surface(data_dir_pbs, mev_counts, 'pbs', 'figures/pbs_smooth_3d_surface.png')
    plot_smooth_3d_surface(data_dir_pos, mev_counts, 'pos', 'figures/pos_smooth_3d_surface.png')

