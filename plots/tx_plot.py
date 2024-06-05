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
        characteristic = float(params[1].replace('.csv', ''))
        return mev_builders, characteristic
    except Exception:
        return None, None

def reshape_data(data, mev_builders, characteristic):
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
            subset['connectivity'] = characteristic
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
    mev_builders, characteristic = extract_params(file_name)
    if mev_builders is None or characteristic is None:
        return pd.DataFrame()
    
    return reshape_data(data, mev_builders, characteristic)

def plot_inclusion_time_subplots(data_dict, save_dir):
    fig, axes = plt.subplots(2, 3, figsize=(18, 12), sharex=True, sharey=True)
    axes = axes.flatten()

    for ax, (file_label, data) in zip(axes, data_dict.items()):
        data['inclusion_time'] = data['block_index'] - data['block_time']
        data['mev_exploited'] = data['mev'] > 0

        inclusion_time_counts = data.groupby(['inclusion_time', 'mev_exploited']).size().unstack(fill_value=0)
        inclusion_time_counts.plot(kind='bar', stacked=True, ax=ax, color={True: 'red', False: 'blue'}, legend=False)
        
        ax.set_xlabel('Inclusion Time (blocks)')
        ax.set_ylabel('Number of Transactions')
        ax.set_title(f'Inclusion Time of Transactions for {file_label}')
        ax.set_ylim(0, 150)

    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(handles, ['Non-MEV', 'MEV'], title='MEV Exploited', loc='upper right')

    plt.tight_layout(rect=[0, 0, 0.9, 1])
    plt.savefig(os.path.join(save_dir, 'inclusion_time_comparison.png'))
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
        plot_inclusion_time_subplots(data_dict, save_dir)

if __name__ == '__main__':
    main()
