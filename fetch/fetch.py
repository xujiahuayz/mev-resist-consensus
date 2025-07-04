import json
import os
import matplotlib.pyplot as plt
from web3 import Web3

# Use your Infura project URL
infura_url = "https://mainnet.infura.io/v3/dd763ae6e7ca4f059f69f4589ad695f0"
web3 = Web3(Web3.HTTPProvider(infura_url))

# Check connection
if not web3.is_connected():
    print("Failed to connect to Ethereum node.")
    exit()

def fetch_block_data(block_number):
    block = web3.eth.get_block(block_number, full_transactions=True)
    return block

def get_transaction_data(txn):
    gas_fee_wei = txn['gasPrice'] * txn['gas']  # Gas fee in wei
    gas_fee_gwei = web3.from_wei(gas_fee_wei, 'gwei')  # Gas fee in Gwei
    receipt = web3.eth.get_transaction_receipt(txn['hash'])
    confirm_time = receipt['blockNumber'] - txn['blockNumber']
    return {
        'hash': txn['hash'].hex(),
        'from': txn['from'],
        'to': txn['to'],
        'value_eth': web3.from_wei(txn['value'], 'ether'),  # Value in Ether
        'value_wei': txn['value'],
        'gas': txn['gas'],
        'gas_price_gwei': web3.from_wei(txn['gasPrice'], 'gwei'),  # Gas price in Gwei
        'gas_price_wei': txn['gasPrice'],
        'gas_fee_gwei': gas_fee_gwei,
        'gas_fee_wei': gas_fee_wei,
        'confirm_time': confirm_time,
        'block_number': txn['blockNumber'],
        'transaction_index': txn['transactionIndex'],
        'nonce': txn['nonce'],
        'input': txn['input'].hex(),
        'receipt_status': receipt['status']
    }

def analyze_block(block_number):
    block = fetch_block_data(block_number)
    block_size = block['size']  # Block size in bytes
    miner = block['miner']
    transactions = block['transactions']
    num_transactions = len(transactions)

    gas_fees = []
    confirm_times = []
    transactions_data = []

    for txn in transactions:
        txn_data = get_transaction_data(txn)
        gas_fees.append(txn_data['gas_fee_gwei'])  # Collect gas fees in Gwei
        confirm_times.append(txn_data['confirm_time'])
        transactions_data.append(txn_data)

    avg_gas_fee = sum(gas_fees) / num_transactions if num_transactions else 0
    avg_confirm_time = sum(confirm_times) / num_transactions if num_transactions else 0
    total_gas_fees = sum(gas_fees)  # Total gas fees in Gwei

    return {
        'block_number': block_number,
        'miner': miner,
        'num_transactions': num_transactions,
        'avg_gas_fee_gwei': avg_gas_fee,
        'avg_confirm_time_blocks': avg_confirm_time,
        'block_size_bytes': block_size,
        'total_gas_fees_gwei': total_gas_fees,
        'transactions': transactions_data,
        'gas_fees_gwei': gas_fees  # List of gas fees in Gwei for distribution analysis
    }

def plot_gas_fee_distribution(gas_fees):
    plt.figure(figsize=(10, 6))
    plt.hist(gas_fees, bins=50, color='blue', edgecolor='black', alpha=0.7)
    plt.title('Gas Fee Distribution (Gwei)')
    plt.xlabel('Gas Fee (Gwei)')
    plt.ylabel('Frequency')
    plt.grid(True)
    plt.show()

def main():
    # Ensure the directory exists
    output_dir = 'data/fetch'
    os.makedirs(output_dir, exist_ok=True)

    block_number = web3.eth.block_number
    blocks_to_analyze = 10
    all_gas_fees = []

    for i in range(block_number, block_number - blocks_to_analyze, -1):
        block_data = analyze_block(i)
        all_gas_fees.extend(block_data['gas_fees_gwei'])  # Collect gas fees from all blocks

        # Save each block's data to a JSON file
        output_file = os.path.join(output_dir, f'block_{block_data["block_number"]}.json')
        with open(output_file, 'w') as f:
            json.dump(block_data, f, indent=4, default=str)

    print(f"Block data analysis saved in '{output_dir}'")

    # Plot gas fee distribution
    plot_gas_fee_distribution(all_gas_fees)

if __name__ == "__main__":
    main()
