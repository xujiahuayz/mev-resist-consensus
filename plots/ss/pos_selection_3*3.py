import csv
import os
import matplotlib.pyplot as plt
import numpy as np

# Change these to match your actual total counts
TOTAL_VALIDATORS = 20
TOTAL_USERS = 50

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
            # Extract numeric part of validator ID
            validator_index = int(validator_id.split('_')[-1])

            # If new block, store the old block's counts
            if block_num != current_block:
                if current_block != -1:
                    attacking_counts.append(attacking_in_block)
                    non_attacking_counts.append(non_attacking_in_block)
                current_block = block_num
                attacking_in_block = 0
                non_attacking_in_block = 0

            # Increment attacking or non-attacking count
            if validator_index < validator_attack_count:
                attacking_in_block += 1
            else:
                non_attacking_in_block += 1

        # Append the last block's data
        attacking_counts.append(attacking_in_block)
        non_attacking_counts.append(non_attacking_in_block)

    return attacking_counts, non_attacking_counts

def plot_cumulative_selections_over_blocks(data_folder, configs):
    """
    - 3×3 subplots
    - Columns = % of attacking validators
    - Rows = % of attacking users
    - Y-axis ticks forced to [0, 500, 1000]
    - Single text labels around the edges:
       * "Percentage of Attacking Validators" (top)
       * "Percentage of Attacking Users" (right)
       * "Cumulative Selections" (left)
       * "Block Number" (bottom)
    """
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Gather unique validator/user counts
    validator_counts = sorted({cfg[0] for cfg in configs})
    user_counts = sorted({cfg[1] for cfg in configs})

    # Create subplots: rows=users, cols=validators
    fig, axes = plt.subplots(
        nrows=len(user_counts),
        ncols=len(validator_counts),
        figsize=(9.5, 9),
        squeeze=False
    )

    # Font sizes
    label_font_size = 16
    tick_label_font_size = 16
    outer_label_font_size = 20

    # Common y-limit
    y_limit = 1000

    # For collecting single legend
    handles, labels = [], []

    for validator_attack_count, user_attack_count in configs:
        row = user_counts.index(user_attack_count)
        col = validator_counts.index(validator_attack_count)
        ax = axes[row, col]

        filename = f"pos_block_data_validators{validator_attack_count}_users{user_attack_count}.csv"
        file_path = os.path.join(data_folder, filename)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            ax.text(0.5, 0.5, "File Not Found",
                    ha='center', va='center',
                    fontsize=label_font_size)
            ax.set_axis_off()
            continue

        att_counts, nonatt_counts = get_validator_counts_by_block(file_path, validator_attack_count)
        block_nums = np.arange(len(att_counts))

        # Plot cumulative sums
        line1, = ax.plot(block_nums, np.cumsum(att_counts),
                         color='red', alpha=0.5, label=r"$\tau_{V_i} = \mathtt{attack}$")
        line2, = ax.plot(block_nums, np.cumsum(nonatt_counts),
                         color='blue', alpha=0.5, label=r"$\tau_{V_i} = \mathtt{benign}$")
        ax.set_ylim(0, y_limit)
        ax.set_yticks([0, 500, 1000])

        # Collect legend refs once
        if not handles:
            handles.extend([line1, line2])
            labels.extend([r"$\tau_{V_i} = \mathtt{attack}$", r"$\tau_{V_i} = \mathtt{benign}$"])

        # Hide x labels except bottom row
        if row != len(user_counts) - 1:
            ax.tick_params(axis='x', labelbottom=False)
        # Hide y labels except first column
        if col != 0:
            ax.tick_params(axis='y', labelleft=False)

        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    # Convert numeric validator counts → percentage columns
    for ax, val_count in zip(axes[0], validator_counts):
        pct_validators = (val_count / TOTAL_VALIDATORS) * 100
        ax.set_title(f"{pct_validators:.0f}", fontsize=outer_label_font_size, pad=10)

    # Convert numeric user counts → percentage rows, on the right
    for ax, usr_count in zip(axes[:, -1], user_counts):
        pct_users = (usr_count / TOTAL_USERS) * 100
        ax.annotate(
            f"{pct_users:.0f}",
            xy=(1.06, 0.5),
            xytext=(1.06, 0.5),
            textcoords='axes fraction',
            ha='center',
            va='center',
            rotation=-90,
            fontsize=outer_label_font_size,
            annotation_clip=False
        )

    # Make subplots fit nicely
    plt.tight_layout()
    plt.subplots_adjust(left=0.12, right=0.88, top=0.83, bottom=0.12)

    # Single text labels
    fig.text(
        0.5, 0.91,  # top
        r"MEV-Seeking Validators $\tau_{V_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )
    fig.text(
        0.95, 0.5,  # right
        r"MEV-Seeking Users $\tau_{U_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        rotation=-90,
        fontsize=outer_label_font_size
    )
    fig.text(
        0.03, 0.5,  # left
        "Cumulative Selections",
        ha='center', va='center',
        rotation='vertical',
        fontsize=outer_label_font_size
    )
    fig.text(
        0.5, 0.06,  # bottom
        "Block Number",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )

    # Single legend at bottom-right
    fig.legend(handles, labels, loc='lower right',
               fontsize=label_font_size, frameon=False)

    out_path = os.path.join(output_dir, 'pos_cumulative_selection_3x3_grid.png')
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"3×3 grid plot saved to {out_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pos_visible80'
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_cumulative_selections_over_blocks(data_folder, configs)
