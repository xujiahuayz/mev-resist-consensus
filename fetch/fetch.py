import json
import os
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
    gas_fee = txn['gasPrice'] * txn['gas']
    receipt = web3.eth.get_transaction_receipt(txn['hash'])
    confirm_time = receipt['blockNumber'] - txn['blockNumber']
    return {
        'hash': txn['hash'].hex(),
        'from': txn['from'],
        'to': txn['to'],
        'value': txn['value'],
        'gas': txn['gas'],
        'gas_price': txn['gasPrice'],
        'gas_fee': gas_fee,
        'confirm_time': confirm_time,
        'block_number': txn['blockNumber'],
        'transaction_index': txn['transactionIndex'],
        'nonce': txn['nonce'],
        'input': txn['input'].hex(),
        'receipt_status': receipt['status']
    }

def analyze_block(block_number):
    block = fetch_block_data(block_number)
    block_size = block['size']
    transactions = block['transactions']
    num_transactions = len(transactions)
    
    gas_fees = []
    confirm_times = []
    transactions_data = []
    
    for txn in transactions:
        txn_data = get_transaction_data(txn)
        gas_fees.append(txn_data['gas_fee'])
        confirm_times.append(txn_data['confirm_time'])
        transactions_data.append(txn_data)
    
    avg_gas_fee = sum(gas_fees) / num_transactions if num_transactions else 0
    avg_confirm_time = sum(confirm_times) / num_transactions if num_transactions else 0
    
    return {
        'block_number': block_number,
        'num_transactions': num_transactions,
        'avg_gas_fee': avg_gas_fee,
        'avg_confirm_time': avg_confirm_time,
        'block_size': block_size,
        'transactions': transactions_data
    }

def main():
    # Ensure the directory exists
    output_dir = 'data/fetch'
    os.makedirs(output_dir, exist_ok=True)
    
    block_number = web3.eth.block_number
    blocks_to_analyze = 10
    
    for i in range(block_number, block_number - blocks_to_analyze, -1):
        block_data = analyze_block(i)
        
        # Save each block's data to a JSON file
        output_file = os.path.join(output_dir, f'block_{block_data["block_number"]}.json')
        with open(output_file, 'w') as f:
            json.dump(block_data, f, indent=4)
    
    print(f"Block data analysis saved in '{output_dir}'")

if __name__ == "__main__":
    main()
