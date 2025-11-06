"""
Fetch Flashbots MEV data for baseline comparison in simulation.

This module fetches blocks that likely contain Flashbots MEV bundles and extracts
MEV-related metrics for use as a baseline in your MEV-resistant consensus simulation.

Note: This uses heuristics to identify MEV blocks. For more comprehensive Flashbots data,
you can also access:
- Flashbots Data Browser: https://flashbots-data.s3.us-east-2.amazonaws.com
- Flashbots MEV Dashboard: https://www.alchemy.com/dapps/flashbots-mev-analytics
"""

import json
import os
import sys
import time
from typing import Dict, List, Optional, Any
from web3 import Web3

# Use your Infura project URL
INFURA_URL = "https://mainnet.infura.io/v3/dd763ae6e7ca4f059f69f4589ad695f0"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

# Check connection
if not web3.is_connected():
    print("Failed to connect to Ethereum node.")
    sys.exit()

# Flashbots builder addresses (known Flashbots builders)
FLASHBOTS_BUILDERS = [
    "0x0000000000000000000000000000000000000000",  # Placeholder - actual builders vary
    # Add more known Flashbots builder addresses as needed
]

# Flashbots MEV-Boost relay endpoints
FLASHBOTS_RELAY_URL = "https://relay.flashbots.net"
FLASHBOTS_DATA_BROWSER = "https://flashbots-data.s3.us-east-2.amazonaws.com"

def is_flashbots_block(block_number: int) -> bool:
    """
    Check if a block was built by Flashbots by examining the block structure.
    Flashbots blocks typically have:
    - Coinbase transaction with specific patterns
    - Builder address in extraData or via MEV-Boost
    """
    try:
        block = web3.eth.get_block(block_number, full_transactions=True)
        
        # Check if block has transactions
        if not block['transactions']:
            return False
        
        # Flashbots blocks often have the first transaction as coinbase
        # and may have specific patterns in the block
        # Check for MEV-Boost patterns (builder address in extraData)
        extra_data = block.get('extraData', b'').hex()
        
        # Check if block was built via MEV-Boost (simplified check)
        # In practice, you'd check the MEV-Boost API or block metadata
        # For now, we'll use heuristics based on transaction patterns
        
        # Flashbots bundles often have specific transaction ordering
        # and gas price patterns
        return _has_mev_patterns(block)
    except Exception as e:
        print(f"Error checking Flashbots block {block_number}: {e}")
        return False

def _has_mev_patterns(block: Dict) -> bool:
    """Heuristic check for MEV patterns in block."""
    transactions = block.get('transactions', [])
    if len(transactions) < 2:
        return False
    
    # Check for backrun/frontrun patterns
    # High-value transactions followed by arbitrage opportunities
    values = [tx.get('value', 0) for tx in transactions]
    gas_prices = [tx.get('gasPrice', 0) for tx in transactions if 'gasPrice' in tx]
    
    # MEV blocks often have:
    # 1. High gas prices (competitive bidding)
    # 2. Multiple high-value transactions
    # 3. Specific transaction ordering
    
    if gas_prices:
        avg_gas_price = sum(gas_prices) / len(gas_prices)
        # High average gas price might indicate MEV competition
        if avg_gas_price > web3.to_wei(100, 'gwei'):  # Threshold for high gas
            return True
    
    # Check for large value transfers (potential MEV opportunities)
    large_values = [v for v in values if v > web3.to_wei(10, 'ether')]
    if len(large_values) >= 2:
        return True
    
    return False

def fetch_flashbots_block_data(block_number: int) -> Optional[Dict[str, Any]]:
    """
    Fetch and analyze a block that likely contains Flashbots bundles.
    Returns detailed MEV metrics for baseline comparison.
    """
    try:
        block = web3.eth.get_block(block_number, full_transactions=True)
        
        if not block:
            return None
        
        transactions = block['transactions']
        num_transactions = len(transactions)
        
        # Analyze transactions for MEV patterns
        mev_metrics = analyze_mev_patterns(block, transactions)
        
        # Calculate standard metrics
        gas_fees = []
        transaction_values = []
        transactions_data = []
        
        for txn in transactions:
            try:
                gas_price = txn.get('gasPrice', 0)
                gas_used = txn.get('gas', 0)
                gas_fee_wei = gas_price * gas_used
                gas_fee_gwei = web3.from_wei(gas_fee_wei, 'gwei')
                
                value_eth = web3.from_wei(txn.get('value', 0), 'ether')
                
                gas_fees.append(gas_fee_gwei)
                transaction_values.append(value_eth)
                
                transactions_data.append({
                    'hash': txn['hash'].hex(),
                    'from': txn.get('from', ''),
                    'to': txn.get('to', ''),
                    'value_eth': value_eth,
                    'gas_price_gwei': web3.from_wei(gas_price, 'gwei') if gas_price else 0,
                    'gas_fee_gwei': gas_fee_gwei,
                    'block_number': block_number,
                    'transaction_index': txn.get('transactionIndex', 0),
                })
            except Exception as e:
                print(f"Error processing transaction in block {block_number}: {e}")
                continue
        
        avg_gas_fee = sum(gas_fees) / num_transactions if num_transactions else 0
        total_gas_fees = sum(gas_fees)
        total_value = sum(transaction_values)
        
        return {
            'block_number': block_number,
            'miner': block.get('miner', ''),
            'num_transactions': num_transactions,
            'avg_gas_fee_gwei': avg_gas_fee,
            'total_gas_fees_gwei': total_gas_fees,
            'total_value_eth': total_value,
            'block_size_bytes': block.get('size', 0),
            'timestamp': block.get('timestamp', 0),
            'gas_limit': block.get('gasLimit', 0),
            'gas_used': block.get('gasUsed', 0),
            'base_fee_per_gas': web3.from_wei(block.get('baseFeePerGas', 0), 'gwei') if block.get('baseFeePerGas') else 0,
            'mev_metrics': mev_metrics,
            'transactions': transactions_data,
            'gas_fees_gwei': gas_fees,
            'is_flashbots_block': True,  # Marked as Flashbots block
        }
    except Exception as e:
        print(f"Error fetching Flashbots block {block_number}: {e}")
        return None

def analyze_mev_patterns(block: Dict, transactions: List) -> Dict[str, Any]:
    """
    Analyze block for MEV extraction patterns.
    Returns metrics useful for baseline comparison.
    """
    if not transactions:
        return {
            'mev_opportunities': 0,
            'high_value_txns': 0,
            'arbitrage_likely': False,
            'frontrun_likely': False,
            'backrun_likely': False,
            'avg_gas_price_gwei': 0,
            'max_gas_price_gwei': 0,
        }
    
    gas_prices = []
    values = []
    high_value_count = 0
    
    for txn in transactions:
        gas_price = txn.get('gasPrice', 0)
        value = txn.get('value', 0)
        
        if gas_price:
            gas_prices.append(web3.from_wei(gas_price, 'gwei'))
        if value:
            values.append(web3.from_wei(value, 'ether'))
            if value > web3.to_wei(1, 'ether'):  # High value threshold
                high_value_count += 1
    
    # Heuristic: Check for MEV patterns
    # Frontrun: High gas price transaction early in block
    # Backrun: High gas price transaction after high-value transaction
    frontrun_likely = False
    backrun_likely = False
    
    if len(transactions) >= 2 and gas_prices:
        # Check if first transaction has high gas price (potential frontrun)
        first_gas = web3.from_wei(transactions[0].get('gasPrice', 0), 'gwei')
        if first_gas > 50:  # Threshold
            frontrun_likely = True
        
        # Check for backrun pattern (high gas after high value)
        for i in range(1, len(transactions)):
            prev_value = transactions[i-1].get('value', 0)
            curr_gas = web3.from_wei(transactions[i].get('gasPrice', 0), 'gwei')
            if prev_value > web3.to_wei(0.1, 'ether') and curr_gas > 50:
                backrun_likely = True
                break
    
    avg_gas_price = sum(gas_prices) / len(gas_prices) if gas_prices else 0
    max_gas_price = max(gas_prices) if gas_prices else 0
    
    return {
        'mev_opportunities': high_value_count,
        'high_value_txns': high_value_count,
        'arbitrage_likely': high_value_count >= 2,
        'frontrun_likely': frontrun_likely,
        'backrun_likely': backrun_likely,
        'avg_gas_price_gwei': avg_gas_price,
        'max_gas_price_gwei': max_gas_price,
        'total_value_eth': sum(values) if values else 0,
    }

def find_flashbots_blocks(start_block: int, end_block: int, sample_size: int = 100) -> List[int]:
    """
    Find blocks that likely contain Flashbots bundles in the given range.
    Returns a sample of block numbers.
    """
    print(f"Scanning blocks {start_block} to {end_block} for Flashbots blocks...")
    
    flashbots_blocks = []
    checked = 0
    
    # Sample blocks to check (don't check every block to save time)
    block_range = end_block - start_block + 1
    if block_range > sample_size:
        # Sample evenly across the range
        step = block_range // sample_size
        blocks_to_check = list(range(start_block, end_block + 1, step))[:sample_size]
    else:
        blocks_to_check = list(range(start_block, end_block + 1))
    
    for block_num in blocks_to_check:
        if is_flashbots_block(block_num):
            flashbots_blocks.append(block_num)
        checked += 1
        
        if checked % 10 == 0:
            print(f"Checked {checked}/{len(blocks_to_check)} blocks, found {len(flashbots_blocks)} Flashbots blocks...")
        
        time.sleep(0.1)  # Rate limiting
    
    print(f"Found {len(flashbots_blocks)} Flashbots blocks out of {checked} checked")
    return flashbots_blocks

def fetch_flashbots_period_data(start_block: int, end_block: int, period_name: str, output_dir: str, sample_size: int = 100):
    """
    Fetch Flashbots data for a specific period.
    Finds Flashbots blocks and extracts MEV metrics.
    """
    print(f"Fetching Flashbots data for {period_name} (blocks {start_block} to {end_block})")
    
    period_dir = os.path.join(output_dir, 'flashbots', period_name)
    os.makedirs(period_dir, exist_ok=True)
    
    # Find Flashbots blocks in this period
    flashbots_blocks = find_flashbots_blocks(start_block, end_block, sample_size)
    
    if not flashbots_blocks:
        print(f"No Flashbots blocks found in period {period_name}")
        return 0
    
    successful_blocks = 0
    all_mev_metrics = []
    
    for block_num in flashbots_blocks:
        print(f"Processing Flashbots block {block_num}...")
        block_data = fetch_flashbots_block_data(block_num)
        
        if block_data:
            # Save block data
            output_file = os.path.join(period_dir, f'flashbots_block_{block_data["block_number"]}.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(block_data, f, indent=4, default=str)
            
            all_mev_metrics.append(block_data['mev_metrics'])
            successful_blocks += 1
        
        time.sleep(0.1)  # Rate limiting
    
    # Create summary with aggregated MEV metrics
    if all_mev_metrics:
        summary = {
            'period_name': period_name,
            'start_block': start_block,
            'end_block': end_block,
            'total_flashbots_blocks': successful_blocks,
            'fetch_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'aggregated_mev_metrics': {
                'avg_mev_opportunities': sum(m.get('mev_opportunities', 0) for m in all_mev_metrics) / len(all_mev_metrics),
                'total_high_value_txns': sum(m.get('high_value_txns', 0) for m in all_mev_metrics),
                'frontrun_blocks': sum(1 for m in all_mev_metrics if m.get('frontrun_likely', False)),
                'backrun_blocks': sum(1 for m in all_mev_metrics if m.get('backrun_likely', False)),
                'avg_gas_price_gwei': sum(m.get('avg_gas_price_gwei', 0) for m in all_mev_metrics) / len(all_mev_metrics),
                'max_gas_price_gwei': max((m.get('max_gas_price_gwei', 0) for m in all_mev_metrics), default=0),
            },
            'usage_notes': {
                'baseline_comparison': 'Use this Flashbots data as baseline for MEV extraction comparison',
                'simulation_testing': 'Compare your simulation results against these Flashbots metrics',
            }
        }
        
        summary_file = os.path.join(period_dir, f'{period_name}_FLASHBOTS_SUMMARY.json')
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=4, default=str)
        
        print(f"Created Flashbots summary: {summary_file}")
    
    print(f"Successfully processed {successful_blocks} Flashbots blocks for {period_name}")
    return successful_blocks

def main():
    """Main function to fetch Flashbots data for baseline comparison."""
    output_dir = 'data/fetch'
    os.makedirs(os.path.join(output_dir, 'flashbots'), exist_ok=True)
    
    current_block = web3.eth.block_number
    print(f"Current block number: {current_block}")
    print("Fetching Flashbots MEV data for baseline comparison...")
    
    # Define periods to fetch Flashbots data (same periods as main fetch.py)
    periods = {
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
        'STABLE_POST_MERGE_2023': {
            'start': 17500000,
            'end': 17501000,
            'description': 'Stable period 2023 (post-merge, no major events)',
            'type': 'stable',
            'era': 'post_merge'
        },
    }
    
    total_blocks_fetched = 0
    
    for period_name, period_info in periods.items():
        print(f"\n{'='*80}")
        print(f"Fetching Flashbots data for: {period_info['description']}")
        print(f"Period ID: {period_name}")
        print(f"Type: {period_info['type']} | Era: {period_info['era']}")
        print(f"Blocks: {period_info['start']} to {period_info['end']}")
        print(f"{'='*80}")
        
        blocks_fetched = fetch_flashbots_period_data(
            period_info['start'],
            period_info['end'],
            period_name,
            output_dir,
            sample_size=50  # Sample 50 blocks per period
        )
        
        total_blocks_fetched += blocks_fetched
    
    print(f"\n{'='*80}")
    print("Flashbots data fetching completed!")
    print(f"Total Flashbots blocks fetched: {total_blocks_fetched}")
    print(f"Data saved in '{output_dir}/flashbots'")
    print(f"{'='*80}")
    print("\nThis Flashbots data can be used as a baseline for comparing")
    print("your MEV-resistant consensus simulation results.")

if __name__ == "__main__":
    main()

