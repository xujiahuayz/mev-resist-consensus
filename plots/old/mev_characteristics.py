import pandas as pd
import os
import glob
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from concurrent.futures import ProcessPoolExecutor, as_completed
from scipy.interpolate import griddata
from scipy.ndimage import gaussian_filter

def process_file(file):
    try:
        filename = os.path.basename(file)
        params = filename.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        characteristic = float(params[1].replace('.csv', ''))
        
        df = pd.read_csv(file)
        
        df['mev_builders'] = mev_builders
        df['characteristic'] = characteristic
        df['total_block_value'] = df['gas_captured'] + df['mev_captured']
        df['reward'] = df['gas_captured'] + df['mev_captured'] - df['block_bid']
        
        return df
    except Exception as e:
        print(f"Error processing file {file}: {e}")
        return pd.DataFrame() 
    
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

def create_meshgrid_interpolated(data, value, sigma=2):
    x = data['mev_builders']
    y = data['characteristic']
    z = data[value]

    xi = np.linspace(x.min(), x.max(), 100)
    yi = np.linspace(y.min(), y.max(), 100)
    xi, yi = np.meshgrid(xi, yi)
    zi = griddata((x, y), z, (xi, yi), method='cubic')
    zi = gaussian_filter(zi, sigma=sigma)

    return xi, yi, zi

def create_3d_plot(x, y, z, xlabel, ylabel, zlabel, filename=None):
    figsize = (12, 10)  # Large figure size to fill space with plot
    fig = plt.figure(figsize=figsize)
    ax = fig.add_subplot(111, projection='3d')
    surf = ax.plot_surface(x, y, z, cmap='viridis', alpha=0.8)
    
    # Set axis labels with slight padding for readability
    ax.set_xlabel(xlabel, labelpad=10, fontsize=18)
    ax.set_ylabel(ylabel, labelpad=10, fontsize=18)
    ax.set_zlabel(zlabel, labelpad=10, fontsize=18)

    original_ticks = ax.get_xticks()
    ax.set_xticklabels([0, 20, 40, 60, 80, 100])

    # Adjust margins to nearly eliminate whitespace
    plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
    
    # Save the figure with minimal padding around the image
    if filename:
        plt.savefig(filename, pad_inches=0, dpi=300)
    plt.close(fig)

def plot_total_block_value(grouped_data, save_dir):
    x, y, z = create_meshgrid_interpolated(grouped_data, 'total_block_value')
    create_3d_plot(x, y, z, 'Percentage of MEV Builders', 'Visible Nodes', 'Total Block Value', 
                   os.path.join(save_dir, 'total_block_value.png'))

def plot_block_bid(grouped_data, save_dir):
    x, y, z = create_meshgrid_interpolated(grouped_data, 'block_bid')
    create_3d_plot(x, y, z, 'Percentage of MEV Builders', 'Visible Nodes', 'Winning Block Bid', 
                   os.path.join(save_dir, 'block_bid.png'))

def plot_gas_captured(grouped_data, save_dir):
    x, y, z = create_meshgrid_interpolated(grouped_data, 'gas_captured')
    create_3d_plot(x, y, z, 'Percentage of MEV Builders', 'Visible Nodes', 'Gas Captured', 
                   os.path.join(save_dir, 'gas_captured.png'))

def plot_mev_captured(grouped_data, save_dir):
    x, y, z = create_meshgrid_interpolated(grouped_data, 'mev_captured')
    create_3d_plot(x, y, z, 'Percentage of MEV Builders', 'Visible Nodes', 'MEV Captured', 
                   os.path.join(save_dir, 'mev_captured.png'))

def plot_reward(grouped_data, save_dir):
    x, y, z = create_meshgrid_interpolated(grouped_data, 'reward')
    create_3d_plot(x, y, z, 'Percentage of MEV Builders', 'Visible Nodes', 'Reward', 
                   os.path.join(save_dir, 'reward.png'))

def plot_last_1000_bid_percentage(data, save_dir):
    data = data.groupby(['mev_builders', 'characteristic']).tail(1000).reset_index()
    data['bid_percentage'] = (data['block_bid'] / data['total_block_value']) * 100
    x, y, z = create_meshgrid_interpolated(data, 'bid_percentage')
    create_3d_plot(x, y, z, 'Percentage of MEV Builders', 'Visible Nodes', 'Last 1000 Bid %',
                   os.path.join(save_dir, 'last_1000_bid_percentage.png'))

if __name__ == '__main__':
    csv_path = "/Users/tammy/Downloads/vary_mev_and_characteristic"
    save_dir = "./figures/3d"
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    all_files = glob.glob(os.path.join(csv_path, "*.csv"))
    
    dataframes = []
    
    batch_size = 50
    for i in range(0, len(all_files), batch_size):
        batch_files = all_files[i:i + batch_size]
        process_files_in_batches(batch_files, dataframes)
    
    if dataframes:
        all_data = pd.concat(dataframes, ignore_index=True)
    
        grouped_data = all_data.groupby(['mev_builders', 'characteristic']).mean().reset_index()
        
        plot_total_block_value(grouped_data, save_dir)
        plot_block_bid(grouped_data, save_dir)
        plot_gas_captured(grouped_data, save_dir)
        plot_mev_captured(grouped_data, save_dir)
        plot_reward(grouped_data, save_dir)
        plot_last_1000_bid_percentage(all_data, save_dir)
    else:
        print("No data to plot.")
