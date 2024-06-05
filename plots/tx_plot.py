import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor

def load_csv(file_path):
    df = pd.read_csv(file_path, usecols=lambda column: column.startswith('transaction_id') or column.startswith('gas') or column.startswith('mev') or column.startswith('block_created') or column == 'block_index' or column == 'mev_builders' or column == 'characteristic')
    if 'mev_builders' not in df.columns or 'characteristic' not in df.columns:
        raise KeyError(f"Expected columns 'mev_builders' and 'characteristic' not found in {file_path}")
    return df

def reshape_data(data):
    records = []
    for idx, row in data.iterrows():
        for i in range(100):
            trans_id_col = f'transaction_id.{i}'
            gas_col = f'gas.{i}'
            mev_col = f'mev.{i}'
            block_time_col = f'block_created.{i}'

            if trans_id_col in data.columns and not pd.isna(row[trans_id_col]):
                records.append({
                    'block_index': row['block_index'],
                    'transaction_id': row[trans_id_col],
                    'gas': row[gas_col],
                    'mev': row[mev_col],
                    'block_time': row[block_time_col],
                    'mev_builders': row['mev_builders'],
                    'connectivity': row['characteristic']
                })
    return pd.DataFrame(records)

def process_file(file_path):
    data = load_csv(file_path)
    return reshape_data(data)

def process_folder(folder_path):
    all_records = []
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.csv')]

    with ProcessPoolExecutor() as executor:
        results = executor.map(process_file, files)
        for result in results:
            all_records.append(result)
    
    combined_data = pd.concat(all_records, ignore_index=True)
    return combined_data

def save_plot(fig, save_path):
    fig.savefig(save_path, bbox_inches='tight', pad_inches=0.1, dpi=300)
    plt.close(fig)

def plot_mev_vs_builders(data, save_dir):
    fig = plt.figure(figsize=(10, 6))
    sns.scatterplot(x='mev_builders', y='mev', data=data, alpha=0.6)
    plt.xlabel('Number of MEV Builders')
    plt.ylabel('MEV Captured per Transaction')
    plt.title('MEV Captured per Transaction vs. Number of MEV Builders')
    plt.grid(True)
    save_plot(fig, os.path.join(save_dir, 'mev_vs_builders.png'))

def plot_mev_vs_connectivity(data, save_dir):
    fig = plt.figure(figsize=(10, 6))
    sns.scatterplot(x='connectivity', y='mev', data=data, alpha=0.6)
    plt.xlabel('Connectivity')
    plt.ylabel('MEV Captured per Transaction')
    plt.title('MEV Captured per Transaction vs. Connectivity')
    plt.grid(True)
    save_plot(fig, os.path.join(save_dir, 'mev_vs_connectivity.png'))

def plot_transaction_count_vs_builders(data, save_dir):
    builder_counts = data.groupby('mev_builders')['transaction_id'].count().reset_index()
    builder_counts.columns = ['mev_builders', 'transaction_count']
    fig = plt.figure(figsize=(10, 6))
    sns.barplot(x='mev_builders', y='transaction_count', data=builder_counts, palette="viridis")
    plt.xlabel('Number of MEV Builders')
    plt.ylabel('Number of Transactions')
    plt.title('Number of Transactions vs. Number of MEV Builders')
    plt.grid(True)
    save_plot(fig, os.path.join(save_dir, 'transaction_count_vs_builders.png'))

def plot_transaction_count_vs_connectivity(data, save_dir):
    connectivity_counts = data.groupby('connectivity')['transaction_id'].count().reset_index()
    connectivity_counts.columns = ['connectivity', 'transaction_count']
    fig = plt.figure(figsize=(10, 6))
    sns.barplot(x='connectivity', y='transaction_count', data=connectivity_counts, palette="viridis")
    plt.xlabel('Connectivity')
    plt.ylabel('Number of Transactions')
    plt.title('Number of Transactions vs. Connectivity')
    plt.grid(True)
    save_plot(fig, os.path.join(save_dir, 'transaction_count_vs_connectivity.png'))

def plot_gas_vs_builders(data, save_dir):
    fig = plt.figure(figsize=(10, 6))
    sns.scatterplot(x='mev_builders', y='gas', data=data, alpha=0.6)
    plt.xlabel('Number of MEV Builders')
    plt.ylabel('Gas Used per Transaction')
    plt.title('Gas Used per Transaction vs. Number of MEV Builders')
    plt.grid(True)
    save_plot(fig, os.path.join(save_dir, 'gas_vs_builders.png'))

def plot_gas_vs_connectivity(data, save_dir):
    fig = plt.figure(figsize=(10, 6))
    sns.scatterplot(x='connectivity', y='gas', data=data, alpha=0.6)
    plt.xlabel('Connectivity')
    plt.ylabel('Gas Used per Transaction')
    plt.title('Gas Used per Transaction vs. Connectivity')
    plt.grid(True)
    save_plot(fig, os.path.join(save_dir, 'gas_vs_connectivity.png'))

def plot_mev_heatmap(data, save_dir):
    heatmap_data = data.pivot_table(values='mev', index='mev_builders', columns='connectivity', aggfunc='mean')
    fig = plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap="YlGnBu", cbar_kws={'label': 'Average MEV per Transaction'})
    plt.xlabel('Connectivity')
    plt.ylabel('Number of MEV Builders')
    plt.title('Heatmap of Average MEV per Transaction')
    save_plot(fig, os.path.join(save_dir, 'mev_heatmap.png'))

if __name__ == '__main__':
    folder_path = "/Users/Tammy/Downloads/transaction_data"
    save_dir = "./figures"
    
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    combined_data = pd.DataFrame()  # Initialize combined_data to an empty DataFrame

    try:
        combined_data = process_folder(folder_path)
    except KeyError as e:
        print(f"Error processing files: {e}")
    
    if not combined_data.empty:
        plot_mev_vs_builders(combined_data, save_dir)
        plot_mev_vs_connectivity(combined_data, save_dir)
        plot_transaction_count_vs_builders(combined_data, save_dir)
        plot_transaction_count_vs_connectivity(combined_data, save_dir)
        plot_gas_vs_builders(combined_data, save_dir)
        plot_gas_vs_connectivity(combined_data, save_dir)
        plot_mev_heatmap(combined_data, save_dir)
    else:
        print("No data to plot.")
