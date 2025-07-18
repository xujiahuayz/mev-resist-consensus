import csv
import os
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Constants
TOTAL_VALIDATORS = 20
TOTAL_BUILDERS = 20
TOTAL_USERS = 50

def get_final_percentages(file_path, attack_count):
    """Extract final cumulative percentages at the end of the simulation."""
    attacking_total = 0
    non_attacking_total = 0
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Extract numeric part of ID
            if 'validator_id' in row:
                entity_id = int(row['validator_id'].split('_')[-1])
            elif 'builder_id' in row:
                entity_id = int(row['builder_id'].split('_')[-1])
            else:
                continue
                
            # Count attacker vs. non-attacker
            if entity_id < attack_count:
                attacking_total += 1
            else:
                non_attacking_total += 1
    
    total = attacking_total + non_attacking_total
    if total == 0:
        return 0, 0
    
    attacking_pct = (attacking_total / total) * 100
    non_attacking_pct = (non_attacking_total / total) * 100
    
    return attacking_pct, non_attacking_pct

def create_comparison_bar_chart():
    """Create separate stacked bar charts for POS and PBS."""
    # Set seaborn style
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)
    
    # Configuration for the 3x3 grid - reordered to group by builder percentage first
    configs = [
        (5, 0), (5, 25), (5, 50),    # 25% builders with 0%, 50%, 100% users
        (10, 0), (10, 25), (10, 50), # 50% builders with 0%, 50%, 100% users  
        (15, 0), (15, 25), (15, 50)  # 75% builders with 0%, 50%, 100% users
    ]
    
    # Data paths
    pos_data_folder = 'data/same_seed/pos_visible80'
    pbs_data_folder = 'data/same_seed/pbs_visible80'
    
    # Collect data
    pos_data = []
    pbs_data = []
    
    for validator_count, user_count in configs:
        # POS data
        pos_filename = f"pos_block_data_validators{validator_count}_users{user_count}.csv"
        pos_filepath = os.path.join(pos_data_folder, pos_filename)
        
        if os.path.exists(pos_filepath):
            pos_att, pos_nonatt = get_final_percentages(pos_filepath, validator_count)
            pos_data.append((pos_att, pos_nonatt))
        else:
            print(f"POS file not found: {pos_filepath}")
            pos_data.append((0, 0))
        
        # PBS data
        pbs_filename = f"pbs_block_data_builders{validator_count}_users{user_count}.csv"
        pbs_filepath = os.path.join(pbs_data_folder, pbs_filename)
        
        if os.path.exists(pbs_filepath):
            pbs_att, pbs_nonatt = get_final_percentages(pbs_filepath, validator_count)
            pbs_data.append((pbs_att, pbs_nonatt))
        else:
            print(f"PBS file not found: {pbs_filepath}")
            pbs_data.append((0, 0))
    
    # Configuration labels for POS
    pos_config_labels = [
        f"[{validator_count/TOTAL_VALIDATORS*100:.0f}, {user_count/TOTAL_USERS*100:.0f}]"
        for validator_count, user_count in configs
    ]
    
    # Configuration labels for PBS
    pbs_config_labels = [
        f"[{validator_count/TOTAL_BUILDERS*100:.0f}, {user_count/TOTAL_USERS*100:.0f}]"
        for validator_count, user_count in configs
    ]
    
    y = np.arange(len(configs))
    height = 0.35
    
    # Font sizes
    label_font_size = 24
    tick_label_font_size = 20
    legend_font_size = 20
    
    # Create POS plot
    fig1, ax1 = plt.subplots(figsize=(10, 10))
    
    # POS stacked bars
    pos_attacking = [data[0] for data in pos_data]
    pos_nonattacking = [data[1] for data in pos_data]
    
    # Use seaborn color codes like the example
    sns.set_color_codes("pastel")
    ax1.barh(y, pos_attacking, height, label=r'$\tau_{V_i} = \mathtt{attack}$', 
             color="b")
    
    sns.set_color_codes("muted")
    ax1.barh(y, pos_nonattacking, height, left=pos_attacking, 
             label=r'$\tau_{V_i} = \mathtt{benign}$', color="b")
    
    ax1.set_xlabel('Percentage of Selections at Block 1000 (%)', fontsize=label_font_size)
    ax1.set_ylabel('Attacking class percentage [validator, user]', fontsize=label_font_size)
    ax1.set_yticks(y)
    ax1.set_yticklabels(pos_config_labels, fontsize=tick_label_font_size)
    ax1.legend(fontsize=legend_font_size)
    ax1.set_xlim(0, 100)
    ax1.set_xticks([0, 25, 50, 75, 100])
    ax1.tick_params(axis='both', labelsize=tick_label_font_size)
    
    plt.tight_layout()
    
    # Save POS plot
    pos_out_path = os.path.join(output_dir, 'pos_block_build_proportions.png')
    plt.savefig(pos_out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"POS block build proportions saved to {pos_out_path}")
    
    # Create PBS plot
    fig2, ax2 = plt.subplots(figsize=(10, 10))
    
    # PBS stacked bars
    pbs_attacking = [data[0] for data in pbs_data]
    pbs_nonattacking = [data[1] for data in pbs_data]
    
    # Use seaborn color codes like the example
    sns.set_color_codes("pastel")
    ax2.barh(y, pbs_attacking, height, label=r'$\tau_{B_i} = \mathtt{attack}$', 
             color="b")
    
    sns.set_color_codes("muted")
    ax2.barh(y, pbs_nonattacking, height, left=pbs_attacking, 
             label=r'$\tau_{B_i} = \mathtt{benign}$', color="b")
    
    ax2.set_xlabel('Percentage of Selections at Block 1000 (%)', fontsize=label_font_size)
    ax2.set_ylabel('Attacking class percentage [builder, user]', fontsize=label_font_size)
    ax2.set_yticks(y)
    ax2.set_yticklabels(pbs_config_labels, fontsize=tick_label_font_size)
    ax2.legend(fontsize=legend_font_size)
    ax2.set_xlim(0, 100)
    ax2.set_xticks([0, 25, 50, 75, 100])
    ax2.tick_params(axis='both', labelsize=tick_label_font_size)
    
    plt.tight_layout()
    
    # Save PBS plot
    pbs_out_path = os.path.join(output_dir, 'pbs_block_build_proportions.png')
    plt.savefig(pbs_out_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"PBS block build proportions saved to {pbs_out_path}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print("=" * 50)
    for i, (validator_count, user_count) in enumerate(configs):
        print(f"Config {i+1} (V{validator_count/TOTAL_VALIDATORS*100:.0f}% U{user_count/TOTAL_USERS*100:.0f}%):")
        print(f"  POS:  {pos_attacking[i]:.1f}% attacking, {pos_nonattacking[i]:.1f}% benign")
        print(f"  PBS:  {pbs_attacking[i]:.1f}% attacking, {pbs_nonattacking[i]:.1f}% benign")
        print()

if __name__ == "__main__":
    create_comparison_bar_chart() 