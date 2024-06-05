import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

def load_csv(file_path):
    try:
        return pd.read_csv(file_path, usecols=lambda column: column.startswith('transaction_id') or column.startswith('gas') or column.startswith('mev') or column.startswith('block_created') or column == 'block_index')
    except Exception:
        return pd.DataFrame()

def extract_params(file_name):
    try:
        params = file_name.split('=')[1:]
        mev_builders = int(params[0].split('characteristic')[0])
        connectivity = float(params[1].replace('.csv', ''))
        return mev_builders, connectivity
    except Exception:
        return None, None

def reshape_data(data, mev_builders, connectivity):
    records = []
    for i in range(100):
        trans_id_col = f'transaction_id.{i}'
        gas_col = f'gas.{i}'
        mev_col = f'mev.{i}'
        block_time_col = f'block_created.{i}'

        if trans_id_col in data.columns:
            subset = data[['block_index', trans_id_col, gas_col, mev_col, block_time_col]].dropna()
            subset.columns = ['block_index', 'transaction_id', 'gas', 'mev', 'block_time']
            subset['mev_builders'] = mev_builders
            subset['connectivity'] = connectivity
            subset['inclusion_time'] = subset['block_index'] - subset['block_time']
            subset = subset[subset['inclusion_time'] >= 0]  # Filter out negative inclusion times
            records.append(subset)
    
    if records:
        return pd.concat(records, ignore_index=True)
    else:
        return pd.DataFrame()

def process_file(file_path):
    data = load_csv(file_path)
    if data.empty:
        return pd.DataFrame()
    
    file_name = os.path.basename(file_path)
    mev_builders, connectivity = extract_params(file_name)
    if mev_builders is None or connectivity is None:
        return pd.DataFrame()
    
    return reshape_data(data, mev_builders, connectivity)

def plot_split_violin(data_dict, save_dir):
    plt.figure(figsize=(18, 12))
    for idx, (file_label, data) in enumerate(data_dict.items(), 1):
        data['mev_exploited'] = data['mev'] > 0
        plt.subplot(2, 3, idx)
        sns.violinplot(data=data, x='mev_builders', y='inclusion_time', hue='mev_exploited', split=True, inner="quart", palette={True: 'lightcoral', False: 'skyblue'})
        plt.title(f'Inclusion Time of Transactions for {file_label}', fontsize=14)
        plt.xlabel('MEV Builders\nConnectivity', fontsize=12)
        plt.ylabel('Inclusion Time (blocks)', fontsize=12)
        plt.legend(title='MEV Exploited', labels=['Non-MEV', 'MEV'], loc='upper right')

    plt.tight_layout()
    plt.savefig(os.path.join(save_dir, 'inclusion_time_violin.png'))
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

    data_dict = {}
    for rep_file in representative_files:
        file_path = os.path.join(folder_path, rep_file)
        data = process_file(file_path)
        if not data.empty:
            data_dict[rep_file.replace(".csv", "")] = data

    if data_dict:
        plot_split_violin(data_dict, save_dir)

if __name__ == '__main__':
    main()
