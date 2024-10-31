import csv
import os
import re
import matplotlib.pyplot as plt
import numpy as np

def get_validator_counts_by_block(file_path, validator_attack_count):
    """Extract validator selection counts by block number from a CSV file."""
    attacking_counts = []
    non_attacking_counts = []

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        current_block = -1
        attacking_in_block = 0
        non_attacking_in_block = 0

        for row in reader:
            block_num = int(row['block_num'])
            validator_id = row['validator_id']
            validator_index = int(validator_id.split('_')[-1])  # Extract numeric part of validator ID

            # Reset counts when a new block is encountered
            if block_num != current_block:
                if current_block != -1:
                    attacking_counts.append(attacking_in_block)
                    non_attacking_counts.append(non_attacking_in_block)
                current_block = block_num
                attacking_in_block = 0
                non_attacking_in_block = 0

            # Increment attacking or non-attacking count based on validator ID
            if validator_index < validator_attack_count:
                attacking_in_block += 1
            else:
                non_attacking_in_block += 1

        # Append the last block's data
        attacking_counts.append(attacking_in_block)
        non_attacking_counts.append(non_attacking_in_block)

    return attacking_counts, non_attacking_counts

def parse_filename(filename):
    """Parse the filename to extract validator and user attack counts."""
    match = re.search(r'validators(\d+)_users(\d+)', filename)
    if match:
        try:
            validator_attack_count = int(match.group(1))
            user_attack_count = int(match.group(2))
            return validator_attack_count, user_attack_count
        except ValueError:
            print(f"Could not parse validator or user attack counts from filename: {filename}")
    else:
        print(f"Skipping file with unexpected format: {filename}")
    return None, None

def plot_cumulative_selections_over_blocks(data_folder, configs):
    """Plot cumulative selections over blocks for specified validator and user attack configurations as a 3x3 grid."""
    # Ensure the output directory exists
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Set up the 3x3 grid
    fig, axes = plt.subplots(3, 3, figsize=(15, 15))
    y_limit = 1000  # Set common y-axis limit for consistency across plots

    # Updated font sizes for better readability
    title_font_size = 20  # Larger font for titles
    label_font_size = 18  # Larger font for axis labels
    legend_font_size = 14  # Larger font for legend
    tick_label_font_size = 14  # Larger font for axis tick labels

    for i, (validator_attack_count, user_attack_count) in enumerate(configs):
        filename = f"pos_block_data_validators{validator_attack_count}_users{user_attack_count}.csv"
        file_path = os.path.join(data_folder, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        attacking_counts, non_attacking_counts = get_validator_counts_by_block(file_path, validator_attack_count)
        block_numbers = list(range(len(attacking_counts)))

        # Locate subplot position
        ax = axes[i // 3, i % 3]
        
        # Plot cumulative selections
        ax.plot(block_numbers, np.cumsum(attacking_counts), label='Attacking Validators', color='red', alpha=0.5)
        ax.plot(block_numbers, np.cumsum(non_attacking_counts), label='Non-Attacking Validators', color='blue', alpha=0.5)
        ax.set_xlabel('Block Number', fontsize=label_font_size)
        ax.set_ylabel('Cumulative Selections', fontsize=label_font_size)
        ax.set_title(f'Attacking Validator Number = {validator_attack_count}\nAttacking User Number = {user_attack_count}', fontsize=title_font_size)
        ax.set_ylim(0, y_limit)
        ax.legend(loc='upper left', fontsize=legend_font_size)
        
        # Set tick label font size for both x and y axes
        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    plt.tight_layout()
    output_path = os.path.join(output_dir, 'pos_cumulative_selection_3x3_grid.png')
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"3x3 grid plot saved to {output_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pos_visible80'
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_cumulative_selections_over_blocks(data_folder, configs)
