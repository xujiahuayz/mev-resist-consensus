import pandas as pd
import os
import matplotlib.pyplot as plt

def load_data(file_path):
    return pd.read_csv(file_path)

def reshape(data):
    transaction_records = []
    for idx, row in data.iterrows():
        for i in range(100):
            trans_id_col = f'transaction_id.{i}'
            gas_col = f'gas.{i}'
            mev_col = f'mev.{i}'
            block_time_col = f'block_created.{i}'

            if trans_id_col in data.columns and not pd.isna(row[trans_id_col]):
                transaction_records.append({
                    'block_index': row['block_index'],
                    'transaction_id': row[trans_id_col],
                    'gas': row[gas_col],
                    'mev': row[mev_col],
                    'block_time': row[block_time_col]
                })
    return pd.DataFrame(transaction_records)

def process_files(folder_path):
    all_transactions = []
    
    for file_name in os.listdir(folder_path):
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            data = load_data(file_path)
            transaction_data_long = reshape(data)
            all_transactions.append(transaction_data_long)
    
    combined_data = pd.concat(all_transactions, ignore_index=True)
    return combined_data

def plot_mev_transactions(data):
    mev_transactions = data[data['mev'] > 0]
    plt.figure(figsize=(10, 6))
    plt.hist(mev_transactions['block_index'], bins=range(1, int(data['block_index'].max()) + 2), edgecolor='black')
    plt.xlabel('Block Index')
    plt.ylabel('Number of MEV Transactions')
    plt.title('Number of MEV Transactions Processed per Block')
    plt.grid(True)
    plt.show()

def plot_block_time_distribution(data):
    plt.figure(figsize=(10, 6))
    plt.hist(data['block_time'], bins=20, edgecolor='black')
    plt.xlabel('Block Time')
    plt.ylabel('Number of Transactions')
    plt.title('Distribution of Block Time for Transactions to be Included')
    plt.grid(True)
    plt.show()


if __name__ == '__main__':
    folder_path = "/Users/Tammy/Downloads/transaction_data"
    combined_data = process_files(folder_path)
    
    plot_mev_transactions(combined_data)
    plot_block_time_distribution(combined_data)
