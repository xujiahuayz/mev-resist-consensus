import csv
import os
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
            builder_index = int(builder_id.split('_')[-1])

            if block_num != current_block:
                if current_block != -1:
                    attacking_counts.append(attacking_in_block)
                    non_attacking_counts.append(non_attacking_in_block)
                current_block = block_num
                attacking_in_block = 0
                non_attacking_in_block = 0

            if builder_index < builder_attack_count:
                attacking_in_block += 1
            else:
                non_attacking_in_block += 1

        # Append final block's data
        attacking_counts.append(attacking_in_block)
        non_attacking_counts.append(non_attacking_in_block)

    return attacking_counts, non_attacking_counts

def plot_cumulative_selections_over_blocks(data_folder, configs):
    """
    3×3 grid:
      * Columns = attacking builders (labeled up top).
      * Rows = attacking users (labeled on the right).
      * Single y-label (“Cumulative Selections”) on the left edge.
      * Single x-label (“Block Number”) at the bottom.
    """
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Gather unique builder/user counts
    builder_counts = sorted({c[0] for c in configs})
    user_counts = sorted({c[1] for c in configs})

    # Create subplots: rows = user counts, cols = builder counts
    fig, axes = plt.subplots(
        nrows=len(user_counts),
        ncols=len(builder_counts),
        figsize=(9.5, 9),
        squeeze=False
    )

    # Font sizes
    label_font_size = 12
    tick_label_font_size = 12
    outer_label_font_size = 16

    # Common y-limit
    y_limit = 1000

    # For a single legend
    handles, labels = [], []

    # Iterate over each configuration
    for builder_attack_count, user_attack_count in configs:
        row = user_counts.index(user_attack_count)
        col = builder_counts.index(builder_attack_count)
        ax = axes[row, col]

        filename = f"pbs_block_data_builders{builder_attack_count}_users{user_attack_count}.csv"
        file_path = os.path.join(data_folder, filename)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            ax.text(0.5, 0.5, "File Not Found",
                    ha='center', va='center', fontsize=label_font_size)
            ax.set_axis_off()
            continue

        attacking_counts, non_attacking_counts = get_builder_counts_by_block(
            file_path, builder_attack_count
        )
        x_values = np.arange(len(attacking_counts))

        line1, = ax.plot(x_values, np.cumsum(attacking_counts),
                         color='red', alpha=0.5,
                         label='Attacking Builders')
        line2, = ax.plot(x_values, np.cumsum(non_attacking_counts),
                         color='blue', alpha=0.5,
                         label='Non-Attacking Builders')
        ax.set_ylim(0, y_limit)

        # Add legend handles only once
        if not handles:
            handles.extend([line1, line2])
            labels.extend(['Attacking Builders', 'Non-Attacking Builders'])

        # Show x-ticks only on the bottom row, but no x-axis label
        if row != len(user_counts) - 1:
            ax.tick_params(axis='x', labelbottom=False)

        # Show y-ticks only on the first column
        if col != 0:
            ax.tick_params(axis='y', labelleft=False)

        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    # Top titles for attacking builders
    for ax, bcount in zip(axes[0], builder_counts):
        ax.set_title(f"Attacking Builders: {bcount}",
                     fontsize=outer_label_font_size, pad=20)

    # Right labels for attacking users
    for ax, ucount in zip(axes[:, -1], user_counts):
        ax.annotate(
            f"Attacking Users: {ucount}",
            xy=(1.05, 0.5), xytext=(1.05, 0.5),
            textcoords='axes fraction',
            ha='center', va='center',
            rotation=-90,
            fontsize=outer_label_font_size,
            annotation_clip=False
        )

    # Single y-label on the left
    fig.text(
        0.04, 0.5, "Cumulative Selections",
        va='center', rotation='vertical',
        fontsize=outer_label_font_size
    )

    # Single x-label at bottom
    fig.text(
        0.5, 0.04, "Block Number",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )

    # One legend for the entire figure
    fig.legend(handles, labels, loc='lower right',
               fontsize=label_font_size, frameon=False)

    # Make space for labels
    plt.tight_layout(rect=[0.05, 0.06, 1, 1])
    out_path = os.path.join(output_dir, "pbs_cumulative_selection_3x3_grid.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"3x3 grid plot saved to {out_path}")

if __name__ == "__main__":
    data_folder = 'data/same_seed/pbs_visible80'
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_cumulative_selections_over_blocks(data_folder, configs)
