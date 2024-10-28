import csv
import os
import re
import matplotlib.pyplot as plt
import numpy as np

def get_builder_counts_by_block(file_path, builder_attack_count):
    """Extract builder selection counts by block number from a CSV file."""
    attacking_counts = []
    non_attacking_counts = []

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        current_block = -1
        attacking_in_block = 0
        non_attacking_in_block = 0

        for row in reader:
            block_num = int(row['block_num'])
            builder_id = row['builder_id']
            builder_index = int(builder_id.split('_')[-1])  # Extract numeric part of builder ID

            # Reset counts when a new block is encountered
            if block_num != current_block:
                if current_block != -1:
                    attacking_counts.append(attacking_in_block)
                    non_attacking_counts.append(non_attacking_in_block)
                current_block = block_num
                attacking_in_block = 0
                non_attacking_in_block = 0

            # Increment attacking or non-attacking count based on builder ID
            if builder_index < builder_attack_count:
                attacking_in_block += 1
            else:
                non_attacking_in_block += 1

        # Append the last block's data
        attacking_counts.append(attacking_in_block)
        non_attacking_counts.append(non_attacking_in_block)

    return attacking_counts, non_attacking_counts

def parse_filename(filename):
    """Parse the filename to extract builder and user attack counts."""
    match = re.search(r'builders(\d+)_users(\d+)', filename)
    if match:
        try:
            builder_attack_count = int(match.group(1))
            user_attack_count = int(match.group(2))
            return builder_attack_count, user_attack_count
        except ValueError:
            print(f"Could not parse builder or user attack counts from filename: {filename}")
    else:
        print(f"Skipping file with unexpected format: {filename}")
    return None, None

def plot_cumulative_selections_over_blocks(data_folder, configs):
    """Plot cumulative selections over blocks for specified builder and user attack configurations."""
    plt.figure(figsize=(15, 10))
    
    for i, (builder_attack_count, user_attack_count) in enumerate(configs):
        filename = f"pbs_block_data_builders{builder_attack_count}_users{user_attack_count}.csv"
        file_path = os.path.join(data_folder, filename)
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        attacking_counts, non_attacking_counts = get_builder_counts_by_block(file_path, builder_attack_count)
        block_numbers = list(range(len(attacking_counts)))

        # Plotting the cumulative selections for this configuration
        plt.subplot(3, 3, i + 1)
        plt.plot(block_numbers, np.cumsum(attacking_counts), label='Attacking Builders', color='red')
        plt.plot(block_numbers, np.cumsum(non_attacking_counts), label='Non-Attacking Builders', color='blue')
        plt.xlabel('Block Number')
        plt.ylabel('Cumulative Selections')
        plt.title(f'Builders {builder_attack_count}, Users {user_attack_count}')
        plt.legend()

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_cumulative_selections_over_blocks(data_folder, configs)
