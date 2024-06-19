import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from concurrent.futures import ProcessPoolExecutor, as_completed

# Define consistent palette and order
palette = {'normal': 'lightblue', 'attacked': 'lightgreen'}
order = ['normal', 'attacked']

def load_csv(file_path):
    try:
        return pd.read_csv(file_path, usecols=lambda column: column.startswith('transaction_id') or column.startswith('gas') or column.startswith('mev') or column.startswith('block_created') or column == 'block_index' or column.startswith('transaction_type'))
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return pd.DataFrame()

def extract_params(file_name):
    try:
        params = file_name.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        connectivity = float(params[1].replace('.csv', ''))
        return mev_builders, connectivity
    except Exception as e:
        print(f"Error extracting params from {file_name}: {e}")
        return None, None

def reshape_data(data, mev_builders, connectivity):
    records = []
    for i in range(100):
        trans_id_col = f'transaction_id.{i}'
        gas_col = f'gas.{i}'
        mev_col = f'mev.{i}'
        block_time_col = f'block_created.{i}'
        trans_type_col = f'transaction_type.{i}'

        if trans_id_col in data.columns and trans_type_col in data.columns:
            subset = data[['block_index', trans_id_col, gas_col, mev_col, block_time_col, trans_type_col]].dropna()
            subset.columns = ['block_index', 'transaction_id', 'gas', 'mev', 'block_created', 'transaction_type']
            subset['mev_builders'] = mev_builders
            subset['connectivity'] = connectivity

            subset['inclusion_time'] = subset['block_index'].astype(int) - subset['block_created'].astype(int)
            subset = subset[(subset['inclusion_time'] >= 0) & (subset['mev'] >= 0) & (subset['gas'] >= 0)]
            records.append(subset)
    
    if records:
        return pd.concat(records, ignore_index=True)
    else:
        return pd.DataFrame()

def process_file(file_path):
    data = load_csv(file_path)
    if data.empty:
        print(f"No data found in {file_path}")
        return pd.DataFrame()
    
    file_name = os.path.basename(file_path)
    mev_builders, connectivity = extract_params(file_name)
    if mev_builders is None or connectivity is None:
        print(f"Could not extract parameters from {file_name}")
        return pd.DataFrame()
    
    reshaped_data = reshape_data(data, mev_builders, connectivity)
    if reshaped_data.empty:
        print(f"No valid transactions in {file_path}")
    return reshaped_data

def process_files_in_parallel(file_paths):
    data_dict = {}
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_file, file_path): file_path for file_path in file_paths}
        for future in as_completed(futures):
            file_path = futures[future]
            try:
                data = future.result()
                if not data.empty:
                    file_label = os.path.basename(file_path).replace(".csv", "")
                    data_dict[file_label] = data
                    print(f"Processed {file_label} with {len(data)} records.")
                else:
                    print(f"No data after processing {file_path}")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
    return data_dict

def plot_violin(data_dict, save_dir):
    plt.figure(figsize=(18, 12))
    for idx, (file_label, data) in enumerate(data_dict.items(), 1):
        data = data[data['transaction_type'].isin(['normal', 'attacked'])]
        plt.subplot(2, 3, idx)
        sns.violinplot(data=data, x='transaction_type', y='inclusion_time', inner="quart", palette=palette, order=order)
        mev_builders = data['mev_builders'].iloc[0]
        connectivity = data['connectivity'].iloc[0]
        plt.title(f'MEV builder number = {mev_builders}\nConnectivity = {connectivity}', fontsize=14)
        plt.xlabel('Transaction Type', fontsize=12)
        plt.ylabel('Inclusion Time (blocks)', fontsize=12)
        plt.ylim(0, data['inclusion_time'].max() * 1.1)
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'inclusion_time_violin.png'))
    plt.close()

def plot_kde_mev(data_dict, save_dir):
    plt.figure(figsize=(18, 12))
    for idx, (file_label, data) in enumerate(data_dict.items(), 1):
        data = data[data['transaction_type'].isin(['normal', 'attacked'])]
        plt.subplot(2, 3, idx)
        sns.kdeplot(data=data[data['transaction_type'] == 'normal'], x='inclusion_time', y='mev', fill=True, color='lightblue', label='normal')
        sns.kdeplot(data=data[data['transaction_type'] == 'attacked'], x='inclusion_time', y='mev', fill=True, color='lightgreen', label='attacked')
        mev_builders = data['mev_builders'].iloc[0]
        connectivity = data['connectivity'].iloc[0]
        plt.title(f'MEV builder number = {mev_builders}\nConnectivity = {connectivity}', fontsize=14)
        plt.xlabel('Inclusion Time (blocks)', fontsize=12)
        plt.ylabel('MEV Extracted', fontsize=12)
        plt.legend()
        plt.xlim(0, data['inclusion_time'].max() * 1.1)
        plt.ylim(0, data['mev'].max() * 1.1)
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'kde_mev.png'))
    plt.close()

def plot_kde_gas(data_dict, save_dir):
    plt.figure(figsize=(18, 12))
    for idx, (file_label, data) in enumerate(data_dict.items(), 1):
        data = data[data['transaction_type'].isin(['normal', 'attacked'])]
        plt.subplot(2, 3, idx)
        sns.kdeplot(data=data[data['transaction_type'] == 'normal'], x='inclusion_time', y='gas', fill=True, color='lightblue', label='normal')
        sns.kdeplot(data=data[data['transaction_type'] == 'attacked'], x='inclusion_time', y='gas', fill=True, color='lightgreen', label='attacked')
        mev_builders = data['mev_builders'].iloc[0]
        connectivity = data['connectivity'].iloc[0]
        plt.title(f'MEV builder number = {mev_builders}\nConnectivity = {connectivity}', fontsize=14)
        plt.xlabel('Inclusion Time (blocks)', fontsize=12)
        plt.ylabel('Gas Used', fontsize=12)
        plt.legend()
        plt.xlim(0, data['inclusion_time'].max() * 1.1)
        plt.ylim(0, data['gas'].max() * 1.1)
    
    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'kde_gas.png'))
    plt.close()

def main():
    folder_path = "/Users/Tammy/Downloads/transaction_data"
    save_dir = "./figures"

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)

    representative_files = [
        "mev_builders=1characteristic=0.2.csv",
        "mev_builders=1characteristic=1.csv",
        "mev_builders=25characteristic=0.2.csv",
        "mev_builders=25characteristic=1.csv",
        "mev_builders=49characteristic=0.2.csv",
        "mev_builders=49characteristic=1.csv"
    ]

    file_paths = [os.path.join(folder_path, rep_file) for rep_file in representative_files]
    data_dict = process_files_in_parallel(file_paths)

    if data_dict:
        plot_violin(data_dict, save_dir)
        plot_kde_mev(data_dict, save_dir)
        plot_kde_gas(data_dict, save_dir)

if __name__ == '__main__':
    main()
