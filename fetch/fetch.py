import json
import os
import sys
import time
from web3 import Web3

# Use your Infura project URL
INFURA_URL = "https://mainnet.infura.io/v3/dd763ae6e7ca4f059f69f4589ad695f0"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Check connection
if not web3.is_connected():
    print("Failed to connect to Ethereum node.")
    sys.exit()

def fetch_block_data(block_number):
    try:
        block = web3.eth.get_block(block_number, full_transactions=True)
        return block
    except Exception as e:
        print(f"Error fetching block {block_number}: {e}")
        return None

def get_transaction_data(txn):
    try:
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
    except Exception as e:
        print(f"Error processing transaction {txn['hash'].hex()}: {e}")
        return None

def analyze_block(block_number):
    block = fetch_block_data(block_number)
    if not block:
        return None
        
    block_size = block['size']  # Block size in bytes
    miner = block['miner']
    transactions = block['transactions']
    num_transactions = len(transactions)

    gas_fees = []
    confirm_times = []
    transactions_data = []

    for txn in transactions:
        txn_data = get_transaction_data(txn)
        if txn_data:
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
        'gas_fees_gwei': gas_fees,  # List of gas fees in Gwei for distribution analysis
        'timestamp': block['timestamp']
    }

def fetch_period_data(start_block, end_block, period_name, output_dir):
    """Fetch data for a specific period"""
    print(f"Fetching data for {period_name} (blocks {start_block} to {end_block})")
    
    period_dir = os.path.join(output_dir, period_name)
    os.makedirs(period_dir, exist_ok=True)
    
    successful_blocks = 0
    
    for block_num in range(start_block, end_block + 1):
        print(f"Processing block {block_num}...")
        block_data = analyze_block(block_num)
        
        if block_data:
            # Save each block's data to a JSON file
            output_file = os.path.join(period_dir, f'block_{block_data["block_number"]}.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(block_data, f, indent=4, default=str)
            
            successful_blocks += 1
        
        # Add a small delay to avoid rate limiting
        time.sleep(0.1)
    
    print(f"Successfully processed {successful_blocks} blocks for {period_name}")
    return successful_blocks

def create_period_summary(period_name, period_info, output_dir):
    """Create a summary file for each period with clear identification"""
    summary = {
        'period_name': period_name,
        'description': period_info['description'],
        'era': period_info.get('era', 'unknown'),
        'volatility_type': period_info.get('type', 'unknown'),
        'start_block': period_info['start'],
        'end_block': period_info['end'],
        'total_blocks': period_info['end'] - period_info['start'] + 1,
        'fetch_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'usage_notes': {
            'simulation_testing': f"Use this period for {period_info.get('type', 'unknown')} market condition testing",
            'data_identifier': f"Period: {period_name}, Era: {period_info.get('era', 'unknown')}",
            'recommended_use': f"Compare with other periods to test {period_info.get('type', 'unknown')} vs stable conditions"
        }
    }
    
    summary_file = os.path.join(output_dir, period_name, f'{period_name}_SUMMARY.json')
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=4, default=str)
    
    print(f"Created summary for {period_name}: {summary_file}")

def main():
    # Ensure the directory exists
    output_dir = 'data/fetch'
    os.makedirs(output_dir, exist_ok=True)
    
    current_block = web3.eth.block_number
    print(f"Current block number: {current_block}")
    
    # Define the periods to fetch - clearly organized for simulation testing
    periods = {
        # High Volatility Events
        'USDC_DEPEG_MARCH_2023': {
            'start': 16900000,
            'end': 16901000,
            'description': 'USDC depeg period (March 2023) - High volatility, Post-merge',
            'type': 'high_volatility',
            'era': 'post_merge'
        },
        'FTX_COLLAPSE_NOV_2022': {
            'start': 16000000,
            'end': 16001000,
            'description': 'FTX collapse period (November 2022) - High volatility, Post-merge',
            'type': 'high_volatility',
            'era': 'post_merge'
        },
        'LUNA_CRASH_MAY_2022': {
            'start': 14800000,
            'end': 14801000,
            'description': 'Luna crash period (May 2022) - High volatility, Pre-merge',
            'type': 'high_volatility',
            'era': 'pre_merge'
        },
        
        # Stable Periods for Comparison
        'STABLE_POST_MERGE_2023': {
            'start': 17500000,
            'end': 17501000,
            'description': 'Stable period 2023 (post-merge, no major events)',
            'type': 'stable',
            'era': 'post_merge'
        },
        'STABLE_POST_MERGE_2022': {
            'start': 16000000,
            'end': 16001000,
            'description': 'Stable period 2022 (post-merge, no major events)',
            'type': 'stable',
            'era': 'post_merge'
        },
        'STABLE_PRE_MERGE_2022': {
            'start': 15000000,
            'end': 15001000,
            'description': 'Stable period 2022 (pre-merge, no major events)',
            'type': 'stable',
            'era': 'pre_merge'
        }
    }
    
    total_blocks_fetched = 0
    
    # Fetch data for each period
    for period_name, period_info in periods.items():
        print(f"\n{'='*80}")
        print(f"Fetching data for: {period_info['description']}")
        print(f"Period ID: {period_name}")
        print(f"Type: {period_info['type']} | Era: {period_info['era']}")
        print(f"Blocks: {period_info['start']} to {period_info['end']}")
        print(f"{'='*80}")
        
        blocks_fetched = fetch_period_data(
            period_info['start'], 
            period_info['end'], 
            period_name, 
            output_dir
        )
        
        # Create period summary for easy identification
        create_period_summary(period_name, period_info, output_dir)
        
        total_blocks_fetched += blocks_fetched
    
    print(f"\n{'='*80}")
    print("All data fetching completed!")
    print(f"Total blocks fetched: {total_blocks_fetched}")
    print(f"Data saved in '{output_dir}'")
    print(f"{'='*80}")
    
    # Create overall simulation testing guide
    simulation_guide = {
        'fetch_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total_periods': len(periods),
        'simulation_testing_guide': {
            'high_volatility_testing': {
                'description': 'Test MEV resistance under extreme market conditions',
                'periods': ['USDC_DEPEG_MARCH_2023', 'FTX_COLLAPSE_NOV_2022', 'LUNA_CRASH_MAY_2022'],
                'use_case': 'Compare MEV extraction patterns during market crashes'
            },
            'stable_market_testing': {
                'description': 'Test MEV resistance under normal market conditions',
                'periods': ['STABLE_POST_MERGE_2023', 'STABLE_POST_MERGE_2022', 'STABLE_PRE_MERGE_2022'],
                'use_case': 'Establish baseline behavior for comparison'
            },
            'era_comparison_testing': {
                'description': 'Compare pre-merge (PoW) vs post-merge (PoS) behavior',
                'pre_merge_periods': ['LUNA_CRASH_MAY_2022', 'STABLE_PRE_MERGE_2022'],
                'post_merge_periods': ['USDC_DEPEG_MARCH_2023', 'FTX_COLLAPSE_NOV_2022', 'STABLE_POST_MERGE_2023', 'STABLE_POST_MERGE_2022'],
                'use_case': 'Analyze consensus mechanism impact on MEV resistance'
            }
        },
        'data_structure': {
            'each_period_contains': [
                'Individual block JSON files',
                'Period summary with clear identification',
                'Usage notes for simulation testing'
            ],
            'naming_convention': 'PERIOD_TYPE_ERA_YEAR for easy identification'
        }
    }
    
    guide_file = os.path.join(output_dir, 'SIMULATION_TESTING_GUIDE.json')
    with open(guide_file, 'w', encoding='utf-8') as f:
        json.dump(simulation_guide, f, indent=4, default=str)
    
    print(f"\nSimulation testing guide created: {guide_file}")
    print("\nReady for simulation testing! Each period is clearly identified and organized.")

if __name__ == "__main__":
    main()
