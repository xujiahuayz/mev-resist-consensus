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

def plot_cumulative_selections_over_blocks(data_folder, configs):
    # Ensure the output directory exists
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Extract unique counts of validators and users for row/column labels
    validator_counts = sorted(set(config[0] for config in configs))
    user_counts = sorted(set(config[1] for config in configs))

    # Adjust figsize to maintain square subplots
    fig, axes = plt.subplots(len(user_counts), len(validator_counts), figsize=(9.5, 9), squeeze=False)
    y_limit = 1000  # Set common y-axis limit for consistency across plots

    # Font sizes for readability
    label_font_size = 12
    tick_label_font_size = 12
    outer_label_font_size = 16

    # Create handles for a unified legend
    handles = []
    labels = []

    for i, (validator_attack_count, user_attack_count) in enumerate(configs):
        filename = f"pos_block_data_validators{validator_attack_count}_users{user_attack_count}.csv"
        file_path = os.path.join(data_folder, filename)

        row = user_counts.index(user_attack_count)
        col = validator_counts.index(validator_attack_count)
        ax = axes[row, col]
        
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            ax.text(0.5, 0.5, "File Not Found", ha='center', va='center', fontsize=label_font_size)
            ax.set_axis_off()
            continue
        
        attacking_counts, non_attacking_counts = get_validator_counts_by_block(file_path, validator_attack_count)
        block_numbers = list(range(len(attacking_counts)))

        # Plot cumulative selections without subplot titles
        line1, = ax.plot(block_numbers, np.cumsum(attacking_counts), label='Attacking Validators', color='red', alpha=0.5)
        line2, = ax.plot(block_numbers, np.cumsum(non_attacking_counts), label='Non-Attacking Validators', color='blue', alpha=0.5)
        ax.set_ylim(0, y_limit)
        
        # Add handles and labels for the legend
        if not handles:
            handles.extend([line1, line2])
            labels.extend(['Attacking Validators', 'Non-Attacking Validators'])
        
        if row != len(user_counts) - 1:  # Not bottom row
            ax.tick_params(axis='x', labelbottom=False)  # Hide x-axis labels but keep tick marks
        if col != 0:  # Not leftmost column
            ax.tick_params(axis='y', labelleft=False)  # Hide y-axis labels but keep tick marks

        # Set axis labels only for edge subplots
        if row == len(user_counts) - 1:
            ax.set_xlabel('Block Number', fontsize=label_font_size)
        
        # Set tick label font size
        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    # Add outer titles for rows and columns without "Number"
    for ax, col_val in zip(axes[0], validator_counts):
        ax.set_title(f'Attacking Validators: {col_val}', fontsize=outer_label_font_size, pad=20)
    
    for ax, row_val in zip(axes[:, 0], user_counts):
        ax.annotate(
            f'Attacking Users: {row_val}', 
            xy=(0, 0.5), xytext=(-0.4, 0.5),
            textcoords='axes fraction', ha='center', va='center',
            fontsize=outer_label_font_size, rotation=90, annotation_clip=False
        )
        ax.annotate(
            "Cumulative Selections", 
            xy=(0, 0.5), xytext=(-0.25, 0.5),
            textcoords='axes fraction', ha='center', va='center',
            fontsize=label_font_size, rotation=90, annotation_clip=False
        )

    # Add a single legend to the bottom right
    fig.legend(handles, labels, loc='lower right', fontsize=12, frameon=False)

    plt.tight_layout(rect=[0, 0.05, 1, 1])  # Adjust layout to fit the legend
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
