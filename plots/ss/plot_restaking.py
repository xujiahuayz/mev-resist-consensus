#!/usr/bin/env python3
"""
Seaborn-based Restaking Plots: Three separate plots for PoS, PBS Builders, and PBS Proposers
Shows stake evolution over time with flare/crest color schemes for attack vs non-attack.
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set Seaborn style
sns.set_style("whitegrid")

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent

def plot_pos_validators():
    """Create PoS validator stake plot."""
    print("Creating PoS validator stake plot...")
    
    # Set random seed for reproducible sampling
    import random
    random.seed(16)
    
    # Load PoS data
    pos_blocks = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pos/restaking_pos_blocks.csv')
    stake_evolution = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pos/stake_evolution.csv')
    
    # Define the 5 initial stake levels (in nano-ETH)
    stake_levels = [32000000000, 64000000000, 96000000000, 160000000000, 256000000000]  # 32, 64, 96, 160, 256 ETH
    
    # Sample validators from each stake level for both attack and non-attack
    # Try to get 2 from each category, but use all available if less than 2
    all_sampled = []
    
    for stake_level in stake_levels:
        # Sample attack validators at this stake level
        attack_at_stake = stake_evolution[(stake_evolution['is_attacker'] == True) & (stake_evolution['initial_stake'] == stake_level)]
        if len(attack_at_stake) >= 1:
            sampled_attack = attack_at_stake.sample(1, random_state=16)['participant_id'].tolist()
            all_sampled.extend(sampled_attack)
        else:
            print(f"Warning: No attack validators at {stake_level/1e9} ETH stake level")
        
        # Sample non-attack validators at this stake level
        nonattack_at_stake = stake_evolution[(stake_evolution['is_attacker'] == False) & (stake_evolution['initial_stake'] == stake_level)]
        if len(nonattack_at_stake) >= 1:
            sampled_nonattack = nonattack_at_stake.sample(1, random_state=16)['participant_id'].tolist()
            all_sampled.extend(sampled_nonattack)
        else:
            print(f"Warning: No non-attack validators at {stake_level/1e9} ETH stake level")
    
    print(f"Total validators sampled: {len(all_sampled)}")
    print(f"Expected: 10 (5 levels × 1 attack × 1 non-attack)")
    print(f"Missing: {10 - len(all_sampled)} validators due to insufficient data at some stake levels")
    
    # Create the plot
    plt.figure(figsize=(18, 12))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot validators organized by attack status and stake level (high to low)
    # First plot attack validators from high to low stake
    attack_validators_ordered = []
    nonattack_validators_ordered = []
    
    for validator_id in all_sampled:
        validator_info = stake_evolution[stake_evolution['participant_id'] == validator_id].iloc[0]
        is_attacker = validator_info['is_attacker']
        initial_stake = validator_info['initial_stake'] / 1e9  # Convert to ETH
        
        if is_attacker:
            attack_validators_ordered.append((validator_id, initial_stake))
        else:
            nonattack_validators_ordered.append((validator_id, initial_stake))
    
    # Sort by stake level (high to low)
    attack_validators_ordered.sort(key=lambda x: x[1], reverse=True)
    nonattack_validators_ordered.sort(key=lambda x: x[1], reverse=True)
    
    # Plot attack validators first (high to low stake)
    attack_labels_added = set()
    for i, (validator_id, initial_stake) in enumerate(attack_validators_ordered):
        validator_data = pos_blocks[pos_blocks['validator_id'] == validator_id]
        
        # Determine color based on stake level
        stake_idx = stake_levels.index(int(initial_stake * 1e9))
        color = attack_colors[stake_idx]
        
        # Only add label for first occurrence of each stake level
        if initial_stake not in attack_labels_added:
            label = f"{initial_stake:.0f} ETH"
            attack_labels_added.add(initial_stake)
        else:
            label = None
        
        sns.lineplot(data=validator_data, 
                    x='block_num', 
                    y=validator_data['validator_capital'] / 1e9,
                    color=color,
                    linewidth=2.5,
                    alpha=0.8,
                    label=label)
    
    # Then plot non-attack validators (high to low stake)
    nonattack_labels_added = set()
    for i, (validator_id, initial_stake) in enumerate(nonattack_validators_ordered):
        validator_data = pos_blocks[pos_blocks['validator_id'] == validator_id]
        
        # Determine color based on stake level
        stake_idx = stake_levels.index(int(initial_stake * 1e9))
        color = nonattack_colors[stake_idx]
        
        # Only add label for first occurrence of each stake level
        if initial_stake not in nonattack_labels_added:
            label = f"{initial_stake:.0f} ETH"
            nonattack_labels_added.add(initial_stake)
        else:
            label = None
        
        sns.lineplot(data=validator_data, 
                    x='block_num', 
                    y=validator_data['validator_capital'] / 1e9,
                    color=color,
                    linewidth=2.5,
                    alpha=0.8,
                    label=label)
    
    # Customize the plot with much larger fonts
    plt.xlabel('Block Number (thousands)', fontsize=42, fontweight='bold')
    plt.ylabel('Stake (ETH)', fontsize=42, fontweight='bold')
    
    # Set x-axis ticks in thousands
    x_ticks = [0, 2000, 4000, 6000, 8000, 10000]
    x_labels = ['0', '2', '4', '6', '8', '10']
    plt.xticks(x_ticks, x_labels, fontsize=36)
    
    # Get the actual data range to set appropriate y-axis limits
    # Find the maximum value across all plotted data
    max_stake = 0
    for validator_id in all_sampled:
        validator_data = pos_blocks[pos_blocks['validator_id'] == validator_id]
        if len(validator_data) > 0:
            max_val = validator_data['validator_capital'].max() / 1e9
            max_stake = max(max_stake, max_val)
    
    # Set y-axis to stop at 600 ETH for PoS
    y_max = 600
    
    # Set explicit y-axis ticks with consistent formatting (every 100 ETH)
    y_ticks = list(range(0, y_max + 1, 100))
    plt.yticks(y_ticks, fontsize=36)
    
    # Set plot to start at (0,0) and end at 10000 blocks
    plt.xlim(left=0, right=10000)
    plt.ylim(bottom=0, top=y_max)
    
    plt.grid(True, alpha=0.3)
    
    # Create custom table-like legend with proper alignment (no box)
    # Get all unique stakes for both categories
    attack_stakes = sorted(list(attack_labels_added), reverse=True)
    benign_stakes = sorted(list(nonattack_labels_added), reverse=True)
    max_stakes = max(len(attack_stakes), len(benign_stakes))
    
    # Position for the legend table with precise spacing
    legend_x = 0.02
    legend_y = 0.98
    row_height = 0.05
    col_width = 0.18
    line_length = 0.03
    
    # Add column headers with consistent font size and perfect alignment
    plt.text(legend_x, legend_y, r'$\tau_{V_i} = \text{attack}$:', 
             transform=plt.gca().transAxes, fontsize=32, weight='bold', va='top')
    plt.text(legend_x + col_width, legend_y, r'$\tau_{V_i} = \text{benign}$:', 
             transform=plt.gca().transAxes, fontsize=32, weight='bold', va='top')
    
    # Add entries in table format with perfect alignment and more spacing from headers
    for i in range(max_stakes):
        row_y = legend_y - row_height * (i + 1.8)
        
        # Attack column
        if i < len(attack_stakes):
            stake = attack_stakes[i]
            stake_idx = stake_levels.index(int(stake * 1e9))
            color = attack_colors[stake_idx]
            # Colored line
            plt.plot([legend_x, legend_x + line_length], [row_y, row_y], 
                    color=color, linewidth=4, transform=plt.gca().transAxes)
            # Text with perfect alignment
            plt.text(legend_x + line_length + 0.02, row_y, f'{stake:.0f} ETH', 
                    transform=plt.gca().transAxes, fontsize=32, va='center', ha='left')
        
        # Benign column
        if i < len(benign_stakes):
            stake = benign_stakes[i]
            stake_idx = stake_levels.index(int(stake * 1e9))
            color = nonattack_colors[stake_idx]
            # Colored line
            plt.plot([legend_x + col_width, legend_x + col_width + line_length], [row_y, row_y], 
                    color=color, linewidth=4, transform=plt.gca().transAxes)
            # Text with perfect alignment
            plt.text(legend_x + col_width + line_length + 0.02, row_y, f'{stake:.0f} ETH', 
                    transform=plt.gca().transAxes, fontsize=32, va='center', ha='left')
    
    # Remove any automatic legend that might appear
    try:
        plt.gca().legend().remove()
    except:
        pass
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pos_validator_stake.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pos_validator_stake.png")

def plot_pbs_builders():
    """Create PBS builder stake plot."""
    print("Creating PBS builder stake plot...")
    
    # Set random seed for reproducible sampling
    import random
    random.seed(16)
    
    # Load PBS data - USE CONTINUOUS STAKE DATA instead of block data
    participants_df = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    continuous_stake_df = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pbs/pbs_restaking_continuous_stake_builders25_users50.csv')
    
    # Filter for builders only
    builders = participants_df[participants_df['participant_type'] == 'builder']
    
    # Define the 5 initial stake levels (in ETH) - same as PoS
    stake_levels = [32, 64, 96, 160, 256]  # 1, 2, 3, 5, 8 nodes respectively
    
    # Sample 1 builder from each stake level for both attack and non-attack
    all_sampled = []
    
    for stake_level in stake_levels:
        # Sample 1 attack builder at this stake level
        attack_at_stake = builders[(builders['is_attacker'] == True) & (builders['initial_stake_eth'] == stake_level)]
        if len(attack_at_stake) >= 1:
            sampled_attack = attack_at_stake.sample(1, random_state=16)['participant_id'].tolist()
            all_sampled.extend(sampled_attack)
        elif len(attack_at_stake) == 1:
            all_sampled.extend(attack_at_stake['participant_id'].tolist())
        else:
            print(f"Warning: No attack builders at {stake_level} ETH stake level")
        
        # Sample 1 non-attack builder at this stake level
        nonattack_at_stake = builders[(builders['is_attacker'] == False) & (builders['initial_stake_eth'] == stake_level)]
        if len(nonattack_at_stake) >= 1:
            sampled_nonattack = nonattack_at_stake.sample(1, random_state=16)['participant_id'].tolist()
            all_sampled.extend(sampled_nonattack)
        elif len(nonattack_at_stake) == 1:
            all_sampled.extend(nonattack_at_stake['participant_id'].tolist())
        else:
            print(f"Warning: No non-attack builders at {stake_level} ETH stake level")
    
    print(f"Total builders sampled: {len(all_sampled)}")
    print(f"Expected: 10 (5 levels × 1 attack × 1 non-attack)")
    print(f"Missing: {10 - len(all_sampled)} builders due to insufficient data at some stake levels")
    
    # Debug: Check what was sampled
    print("\nSampled builders by stake level:")
    for stake_level in stake_levels:
        attack_count = len([b for b in all_sampled if 
                           participants_df[participants_df['participant_id'] == b].iloc[0]['is_attacker'] == True and
                           participants_df[participants_df['participant_id'] == b].iloc[0]['initial_stake_eth'] == stake_level])
        nonattack_count = len([b for b in all_sampled if 
                              participants_df[participants_df['participant_id'] == b].iloc[0]['is_attacker'] == False and
                              participants_df[participants_df['participant_id'] == b].iloc[0]['initial_stake_eth'] == stake_level])
        print(f"{stake_level} ETH: {attack_count} attack, {nonattack_count} non-attack")
    
    # Create the plot
    plt.figure(figsize=(18, 12))
    
    # Color palettes: flare for attackers, crest for non-attackers
    attack_colors = sns.color_palette("flare", n_colors=5)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot builders organized by attack status and stake level (high to low)
    # First plot attack builders from high to low stake
    attack_builders_ordered = []
    nonattack_builders_ordered = []
    
    for participant_id in all_sampled:
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        is_attacker = participant_info['is_attacker']
        initial_stake = participant_info['initial_stake_eth']
        
        if is_attacker:
            attack_builders_ordered.append((participant_id, initial_stake))
        else:
            nonattack_builders_ordered.append((participant_id, initial_stake))
    
    # Sort by stake level (high to low)
    attack_builders_ordered.sort(key=lambda x: x[1], reverse=True)
    nonattack_builders_ordered.sort(key=lambda x: x[1], reverse=True)
    
    # Plot attack builders first (high to low stake)
    attack_labels_added = set()
    for i, (participant_id, initial_stake) in enumerate(attack_builders_ordered):
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        continuous_data = continuous_stake_df[continuous_stake_df['participant_id'] == participant_id]
        
        if len(continuous_data) > 0:
            # Determine color based on stake level
            stake_idx = stake_levels.index(int(initial_stake))
            color = attack_colors[stake_idx]
            
            # Only add label for first occurrence of each stake level
            if initial_stake not in attack_labels_added:
                label = f"{initial_stake:.0f} ETH"
                attack_labels_added.add(initial_stake)
            else:
                label = None
            
            # Plot stake evolution using continuous data (convert to ETH)
            sns.lineplot(data=continuous_data, 
                        x='block_num', 
                        y=continuous_data['current_capital'] / 1e9,  # Use current_capital for total value
                        color=color,
                        linewidth=2.5,
                        alpha=0.8,
                        label=label)
    
    # Then plot non-attack builders (high to low stake)
    nonattack_labels_added = set()
    for i, (participant_id, initial_stake) in enumerate(nonattack_builders_ordered):
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        continuous_data = continuous_stake_df[continuous_stake_df['participant_id'] == participant_id]
        
        if len(continuous_data) > 0:
            # Determine color based on stake level
            stake_idx = stake_levels.index(int(initial_stake))
            color = nonattack_colors[stake_idx]
            
            # Only add label for first occurrence of each stake level
            if initial_stake not in nonattack_labels_added:
                label = f"{initial_stake:.0f} ETH"
                nonattack_labels_added.add(initial_stake)
            else:
                label = None
            
            # Plot stake evolution using continuous data (convert to ETH)
            sns.lineplot(data=continuous_data, 
                        x='block_num', 
                        y=continuous_data['current_capital'] / 1e9,  # Use current_capital for total value
                        color=color,
                        linewidth=2.5,
                        alpha=0.8,
                        label=label)
    
    # Customize the plot with much larger fonts
    plt.xlabel('Block Number (thousands)', fontsize=42, fontweight='bold')
    plt.ylabel('Stake (ETH)', fontsize=42, fontweight='bold')
    
    # Set x-axis ticks in thousands
    x_ticks = [0, 2000, 4000, 6000, 8000, 10000]
    x_labels = ['0', '2', '4', '6', '8', '10']
    plt.xticks(x_ticks, x_labels, fontsize=36)
    
    # Set y-axis to stop at 1000 ETH for PBS builders with 200 ETH intervals
    y_max = 1000
    
    # Set explicit y-axis ticks with consistent formatting (every 200 ETH)
    y_ticks = list(range(0, y_max + 1, 200))
    plt.yticks(y_ticks, fontsize=36)
    
    # Set plot to start at (0,0) and end at 10000 blocks
    plt.xlim(left=0, right=10000)
    plt.ylim(bottom=0, top=y_max)
    
    plt.grid(True, alpha=0.3)
    
    # Create custom table-like legend with proper alignment (no box)
    # Get all unique stakes for both categories
    attack_stakes = sorted(list(attack_labels_added), reverse=True)
    benign_stakes = sorted(list(nonattack_labels_added), reverse=True)
    max_stakes = max(len(attack_stakes), len(benign_stakes))
    
    # Position for the legend table with precise spacing
    legend_x = 0.02
    legend_y = 0.98
    row_height = 0.05
    col_width = 0.18
    line_length = 0.03
    
    # Add column headers with consistent font size and perfect alignment
    plt.text(legend_x, legend_y, r'$\tau_{B_i} = \text{attack}$:', 
             transform=plt.gca().transAxes, fontsize=32, weight='bold', va='top')
    plt.text(legend_x + col_width, legend_y, r'$\tau_{B_i} = \text{benign}$:', 
             transform=plt.gca().transAxes, fontsize=32, weight='bold', va='top')
    
    # Add entries in table format with perfect alignment and more spacing from headers
    for i in range(max_stakes):
        row_y = legend_y - row_height * (i + 1.8)
        
        # Attack column
        if i < len(attack_stakes):
            stake = attack_stakes[i]
            stake_idx = stake_levels.index(int(stake))
            color = attack_colors[stake_idx]
            # Colored line
            plt.plot([legend_x, legend_x + line_length], [row_y, row_y], 
                    color=color, linewidth=4, transform=plt.gca().transAxes)
            # Text with perfect alignment
            plt.text(legend_x + line_length + 0.02, row_y, f'{stake:.0f} ETH', 
                    transform=plt.gca().transAxes, fontsize=32, va='center', ha='left')
        
        # Benign column
        if i < len(benign_stakes):
            stake = benign_stakes[i]
            stake_idx = stake_levels.index(int(stake))
            color = nonattack_colors[stake_idx]
            # Colored line
            plt.plot([legend_x + col_width, legend_x + col_width + line_length], [row_y, row_y], 
                    color=color, linewidth=4, transform=plt.gca().transAxes)
            # Text with perfect alignment
            plt.text(legend_x + col_width + line_length + 0.02, row_y, f'{stake:.0f} ETH', 
                    transform=plt.gca().transAxes, fontsize=32, va='center', ha='left')
    
    # Remove any automatic legend that might appear
    try:
        plt.gca().legend().remove()
    except:
        pass
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pbs_builder_stake.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_builder_stake.png")

def plot_pbs_proposers():
    """Create PBS proposer stake plot."""
    print("Creating PBS proposer stake plot...")
    
    # Set random seed for reproducible sampling
    import random
    random.seed(16)
    
    # Load PBS data - USE CONTINUOUS STAKE DATA instead of block data
    participants_df = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pbs/pbs_restaking_participants_builders25_users50.csv')
    continuous_stake_df = pd.read_csv(PROJECT_ROOT / 'data/same_seed/restaking_pbs/pbs_restaking_continuous_stake_builders25_users50.csv')
    
    # Filter for proposers only (all non-attack in this simulation)
    proposers = participants_df[participants_df['participant_type'] == 'proposer']
    
    # Define the 5 initial stake levels (in ETH) - same as PoS
    stake_levels = [32, 64, 96, 160, 256]  # 1, 2, 3, 5, 8 nodes respectively
    
    # Sample 2 proposers from each stake level
    all_sampled = []
    
    for stake_level in stake_levels:
        proposers_at_stake = proposers[proposers['initial_stake_eth'] == stake_level]
        if len(proposers_at_stake) >= 1:
            sampled_proposers = proposers_at_stake.sample(1, random_state=16)['participant_id'].tolist()
            all_sampled.extend(sampled_proposers)
        else:
            print(f"Warning: No proposers at {stake_level} ETH stake level")
    
    print(f"Total proposers sampled: {len(all_sampled)}")
    print(f"Expected: 5 (5 levels × 1 proposer)")
    print(f"Missing: {5 - len(all_sampled)} proposers due to insufficient data at some stake levels")
    
    # Sort proposers by stake level (high to low)
    proposers_ordered = []
    for participant_id in all_sampled:
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        initial_stake = participant_info['initial_stake_eth']
        proposers_ordered.append((participant_id, initial_stake))
    
    proposers_ordered.sort(key=lambda x: x[1], reverse=True)
    
    # Create the plot
    plt.figure(figsize=(18, 12))
    
    # Color palette: crest for non-attackers (all proposers are non-attack)
    nonattack_colors = sns.color_palette("crest", n_colors=5)
    
    # Plot proposers ordered by stake level (high to low)
    for i, (participant_id, initial_stake) in enumerate(proposers_ordered):
        participant_info = participants_df[participants_df['participant_id'] == participant_id].iloc[0]
        # Use continuous stake data instead of block data
        continuous_data = continuous_stake_df[continuous_stake_df['participant_id'] == participant_id]
        
        if len(continuous_data) > 0:
            # Determine color based on stake level
            stake_idx = stake_levels.index(int(initial_stake))
            color = nonattack_colors[stake_idx]
            
            # Only add label for first occurrence of each stake level
            if i == 0 or proposers_ordered[i-1][1] != initial_stake:
                label = f"{initial_stake:.0f} ETH"
            else:
                label = None
            
            # Plot stake evolution using continuous data (convert to ETH)
            sns.lineplot(data=continuous_data, 
                        x='block_num', 
                        y=continuous_data['current_capital'] / 1e9,  # Use current_capital for total value
                        color=color,
                        linewidth=2.5,
                        alpha=0.8,
                        label=label)
    
    # Customize the plot with much larger fonts
    plt.xlabel('Block Number (thousands)', fontsize=42, fontweight='bold')
    plt.ylabel('Stake (ETH)', fontsize=42, fontweight='bold')
    
    # Set x-axis ticks in thousands
    x_ticks = [0, 2000, 4000, 6000, 8000, 10000]
    x_labels = ['0', '2', '4', '6', '8', '10']
    plt.xticks(x_ticks, x_labels, fontsize=36)
    
    # Set y-axis to stop at 600 ETH for PBS proposers with 200 ETH intervals
    y_max = 600
    
    # Set explicit y-axis ticks with consistent formatting (every 200 ETH)
    y_ticks = list(range(0, y_max + 1, 200))
    plt.yticks(y_ticks, fontsize=36)
    
    # Set plot to start at (0,0) and end at 10000 blocks
    plt.xlim(left=0, right=10000)
    plt.ylim(bottom=0, top=y_max)
    
    plt.grid(True, alpha=0.3)
    
    # Position legend within the plot area at top left with much larger font (no box)
    plt.legend(loc='upper left', fontsize=32, bbox_to_anchor=(0.02, 0.98), frameon=False)
    
    plt.tight_layout()
    plt.savefig(PROJECT_ROOT / 'figures/restake/pbs_proposer_stake.png', 
                dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved: pbs_proposer_stake.png")

def main():
    """Generate all three Seaborn-based plots."""
    print("Generating three separate stake plots...")
    
    # Create figures/restake directory
    figures_dir = PROJECT_ROOT / 'figures/restake'
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate all three plots
    plot_pos_validators()
    plot_pbs_builders()
    plot_pbs_proposers()
    
    print("All three plots completed!")

if __name__ == "__main__":
    main() 