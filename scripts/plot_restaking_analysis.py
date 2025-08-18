"""Plot restaking analysis results showing stake growth over time using seaborn."""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from pathlib import Path

# Set seaborn style and color palette
plt.style.use('default')
sns.set_theme(style="whitegrid")
sns.set_palette("husl")

# Define constants
VALIDATOR_THRESHOLD = 32 * 10**9  # 32 ETH in gwei
ETH_IN_GWEI = 10**9

def load_and_clean_data():
    """Load and clean the simulation data."""
    
    # Load PoS data
    pos_file = Path("data/same_seed/restaking_pos/restaking_pos_blocks.csv")
    pos_data = pd.read_csv(pos_file)
    
    # Load PBS data
    pbs_file = Path("data/same_seed/restaking_pbs/restaking_pbs_blocks.csv")
    pbs_data = pd.read_csv(pbs_file)
    
    return pos_data, pbs_data

def calculate_growth_from_baseline(data, id_col, initial_stake_col, current_stake_col):
    """Calculate growth from initial stake for each participant."""
    # Get the ACTUAL block 0 value for each participant as the baseline
    # Sort by block_num first to ensure we get block 0
    data_sorted = data.sort_values(['block_num', id_col])
    
    # Get the first block (block 0) for each participant
    baseline_stakes = data_sorted.groupby(id_col)[current_stake_col].first().reset_index()
    baseline_stakes = baseline_stakes.rename(columns={current_stake_col: 'baseline_stake'})
    
    # Merge baseline with main data
    data_with_growth = data.merge(baseline_stakes, on=id_col)
    
    # Calculate growth: current stake - baseline stake
    data_with_growth['growth'] = data_with_growth[current_stake_col] - data_with_growth['baseline_stake']
    
    # Debug: verify no negative growth
    negative_growth = data_with_growth[data_with_growth['growth'] < 0]
    if not negative_growth.empty:
        print(f"WARNING: Found {len(negative_growth)} rows with negative growth!")
        print("Sample of negative growth:")
        print(negative_growth[['block_num', id_col, current_stake_col, 'baseline_stake', 'growth']].head())
    
    return data_with_growth

def plot_validator_growth(pos_data):
    """Plot validator stake growth over time using seaborn."""
    
    # Calculate growth from baseline
    pos_growth = calculate_growth_from_baseline(
        pos_data, 'validator_id', 'validator_capital', 'validator_capital'
    )
    
    # Get initial parameters for each validator
    validators = pos_data.groupby('validator_id').agg({
        'is_attacker': 'first'
    }).reset_index()
    
    # Get initial capital for each validator (use first value, not minimum)
    initial_capitals = pos_data.groupby('validator_id')['validator_capital'].first().reset_index()
    validators = validators.merge(initial_capitals, on='validator_id')
    validators = validators.rename(columns={'validator_capital': 'initial_capital'})
    
    # Create stake level categories
    validators['stake_level'] = (validators['initial_capital'] // VALIDATOR_THRESHOLD).astype(int)
    validators['stake_level_label'] = validators['stake_level'].apply(lambda x: f"{x}x32ETH")
    
    # Create parameter groups
    validators['group'] = validators.apply(
        lambda x: f"{'Attacker' if x['is_attacker'] else 'Non-Attacker'}_{x['stake_level_label']}",
        axis=1
    )
    
    # Merge back to get growth data
    pos_growth_with_params = pos_growth.merge(
        validators[['validator_id', 'group', 'stake_level', 'is_attacker', 'stake_level_label']], 
        on='validator_id', how='left'
    )
    
    # Debug: print available columns
    print("Available columns in pos_growth_with_params:", pos_growth_with_params.columns.tolist())
    print("Sample of merged data:")
    print(pos_growth_with_params[['validator_id', 'group', 'stake_level', 'is_attacker_y']].head())
    
    # Debug: show growth calculation
    print("\nGrowth calculation sample:")
    sample_growth = pos_growth_with_params[['validator_id', 'block_num', 'validator_capital', 'baseline_stake', 'growth']].head(10)
    print(sample_growth)
    print(f"Min growth: {pos_growth_with_params['growth'].min()}")
    print(f"Max growth: {pos_growth_with_params['growth'].max()}")
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each group with different colors
    for group_name, group_data in pos_growth_with_params.groupby('group'):
        is_attacker = group_data['is_attacker_y'].iloc[0]
        stake_level = group_data['stake_level'].iloc[0]
        
        # Calculate average growth for this group
        avg_growth = group_data.groupby('block_num')['growth'].mean()
        
        # Color scheme: Red for attackers, Blue for non-attackers
        # Different shades based on stake level
        if is_attacker:
            base_color = 'red'
            alpha = min(0.9, 0.3 + (stake_level * 0.15))
        else:
            base_color = 'blue'
            alpha = min(0.9, 0.3 + (stake_level * 0.15))
        
        ax.plot(avg_growth.index, avg_growth.values / ETH_IN_GWEI, 
                color=base_color, linewidth=2, alpha=alpha, label=group_name)
    
    # Add horizontal lines for whole ETH multiples
    max_growth = pos_growth_with_params['growth'].max() / ETH_IN_GWEI
    for eth_multiple in range(1, int(max_growth) + 1):
        ax.axhline(y=eth_multiple, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
        ax.text(ax.get_xlim()[1] * 0.98, eth_multiple, f'{eth_multiple} ETH', 
                ha='right', va='bottom', fontsize=8, alpha=0.7)
    
    ax.set_xlabel('Block Number')
    ax.set_ylabel('Stake Growth (ETH)')
    ax.set_title('PoS Validator Stake Growth Over Time (All Restaking)')
    ax.set_ylim(bottom=0)  # Growth can never be negative
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/pos_validator_growth.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_builder_growth(pbs_data):
    """Plot builder stake growth over time using seaborn."""
    
    # Calculate growth from baseline
    pbs_growth = calculate_growth_from_baseline(
        pbs_data, 'builder_id', 'builder_stake', 'builder_stake'
    )
    
    # Get initial parameters for each builder
    builders = pbs_data.groupby('builder_id').agg({
        'builder_is_attacker': 'first'
    }).reset_index()
    
    # Get initial capital for each builder (use first value, not minimum)
    initial_capitals = pbs_data.groupby('builder_id')['builder_stake'].first().reset_index()
    builders = builders.merge(initial_capitals, on='builder_id')
    builders = builders.rename(columns={'builder_stake': 'initial_capital'})
    
    # Create stake level categories
    builders['stake_level'] = (builders['initial_capital'] // VALIDATOR_THRESHOLD).astype(int)
    builders['stake_level_label'] = builders['stake_level'].apply(lambda x: f"{x}x32ETH")
    
    # Create parameter groups
    builders['group'] = builders.apply(
        lambda x: f"{'Attacker' if x['builder_is_attacker'] else 'Non-Attacker'}_{x['stake_level_label']}",
        axis=1
    )
    
    # Merge back to get growth data
    pbs_builder_growth = pbs_growth.merge(
        builders[['builder_id', 'group', 'stake_level', 'builder_is_attacker', 'stake_level_label']], 
        on='builder_id', how='left'
    )
    
    # Debug: print available columns
    print("Available columns in pbs_builder_growth:", pbs_builder_growth.columns.tolist())
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each group with different colors
    for group_name, group_data in pbs_builder_growth.groupby('group'):
        is_attacker = group_data['builder_is_attacker_y'].iloc[0]
        stake_level = group_data['stake_level'].iloc[0]
        
        # Calculate average growth for this group
        avg_growth = group_data.groupby('block_num')['growth'].mean()
        
        # Color scheme: Red for attackers, Blue for non-attackers
        if is_attacker:
            base_color = 'red'
            alpha = min(0.9, 0.3 + (stake_level * 0.15))
        else:
            base_color = 'blue'
            alpha = min(0.9, 0.3 + (stake_level * 0.15))
        
        ax.plot(avg_growth.index, avg_growth.values / ETH_IN_GWEI, 
                color=base_color, linewidth=2, alpha=alpha, label=group_name)
    
    # Add horizontal lines for whole ETH multiples
    max_growth = pbs_builder_growth['growth'].max() / ETH_IN_GWEI
    for eth_multiple in range(1, int(max_growth) + 1):
        ax.axhline(y=eth_multiple, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
        ax.text(ax.get_xlim()[1] * 0.98, eth_multiple, f'{eth_multiple} ETH', 
                ha='right', va='bottom', fontsize=8, alpha=0.7)
    
    ax.set_xlabel('Block Number')
    ax.set_ylabel('Stake Growth (ETH)')
    ax.set_title('PBS Builder Stake Growth Over Time (All Restaking)')
    ax.set_ylim(bottom=0)  # Growth can never be negative
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/pbs_builder_growth.png', dpi=300, bbox_inches='tight')
    plt.show()

def plot_proposer_growth(pbs_data):
    """Plot proposer stake growth over time using seaborn."""
    
    # Calculate growth from baseline
    pbs_growth = calculate_growth_from_baseline(
        pbs_data, 'proposer_id', 'proposer_stake', 'proposer_stake'
    )
    
    # Get initial parameters for each proposer
    proposers = pbs_data.groupby('proposer_id').agg({
        'proposer_type': 'first'
    }).reset_index()
    
    # Get initial capital for each proposer (use first value, not minimum)
    initial_capitals = pbs_data.groupby('proposer_id')['proposer_stake'].first().reset_index()
    proposers = proposers.merge(initial_capitals, on='proposer_id')
    proposers = proposers.rename(columns={'proposer_stake': 'initial_capital'})
    
    # Create stake level categories
    proposers['stake_level'] = (proposers['initial_capital'] // VALIDATOR_THRESHOLD).astype(int)
    proposers['stake_level_label'] = proposers['stake_level'].apply(lambda x: f"{x}x32ETH")
    
    # Create parameter groups
    proposers['group'] = proposers.apply(
        lambda x: f"{x['proposer_type'].title()}_{x['stake_level_label']}",
        axis=1
    )
    
    # Merge back to get growth data
    pbs_proposer_growth = pbs_growth.merge(
        proposers[['proposer_id', 'group', 'stake_level', 'proposer_type', 'stake_level_label']], 
        on='proposer_id', how='left'
    )
    
    # Debug: print available columns
    print("Available columns in pbs_proposer_growth:", pbs_proposer_growth.columns.tolist())
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Plot each group with different colors
    for group_name, group_data in pbs_proposer_growth.groupby('group'):
        proposer_type = group_data['proposer_type_y'].iloc[0]
        stake_level = group_data['stake_level'].iloc[0]
        
        # Calculate average growth for this group
        avg_growth = group_data.groupby('block_num')['growth'].mean()
        
        # Color scheme: Green for builder-proposers, Purple for pure proposers
        if proposer_type == 'builder':
            base_color = 'green'
        else:
            base_color = 'purple'
        
        alpha = min(0.9, 0.3 + (stake_level * 0.15))
        
        ax.plot(avg_growth.index, avg_growth.values / ETH_IN_GWEI, 
                color=base_color, linewidth=2, alpha=alpha, label=group_name)
    
    # Add horizontal lines for whole ETH multiples
    max_growth = pbs_proposer_growth['growth'].max() / ETH_IN_GWEI
    for eth_multiple in range(1, int(max_growth) + 1):
        ax.axhline(y=eth_multiple, color='gray', linestyle='--', alpha=0.3, linewidth=0.5)
        ax.text(ax.get_xlim()[1] * 0.98, eth_multiple, f'{eth_multiple} ETH', 
                ha='right', va='bottom', fontsize=8, alpha=0.7)
    
    ax.set_xlabel('Block Number')
    ax.set_ylabel('Stake Growth (ETH)')
    ax.set_title('PBS Proposer Stake Growth Over Time (All Restaking)')
    ax.set_ylim(bottom=0)  # Growth can never be negative
    ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('plots/pbs_proposer_growth.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function to run all plots."""
    
    print("Loading simulation data...")
    pos_data, pbs_data = load_and_clean_data()
    
    print("Creating plots directory...")
    Path("plots").mkdir(exist_ok=True)
    
    print("Plotting PoS validator growth...")
    plot_validator_growth(pos_data)
    
    print("Plotting PBS builder growth...")
    plot_builder_growth(pbs_data)
    
    print("Plotting PBS proposer growth...")
    plot_proposer_growth(pbs_data)
    
    print("All plots completed and saved to 'plots/' directory!")

if __name__ == "__main__":
    main()
