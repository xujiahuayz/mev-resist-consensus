import csv
import os
import matplotlib.pyplot as plt
import numpy as np

# Change these to match the actual total number of builders and users
TOTAL_BUILDERS = 20
TOTAL_USERS = 50

def get_builder_counts_by_block(file_path, builder_attack_count):
    """Extract builder selection counts by block number from a CSV file."""
    attacking_counts = []
    non_attacking_counts = []

    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        current_block = -1
        a_in_block = 0
        na_in_block = 0

        for row in reader:
            block_num = int(row['block_num'])
            builder_id = row['builder_id']
            builder_index = int(builder_id.split('_')[-1])

            if block_num != current_block:
                if current_block != -1:
                    attacking_counts.append(a_in_block)
                    non_attacking_counts.append(na_in_block)
                current_block = block_num
                a_in_block, na_in_block = 0, 0

            # Count attacker vs. non-attacker
            if builder_index < builder_attack_count:
                a_in_block += 1
            else:
                na_in_block += 1

        # Final block's data
        attacking_counts.append(a_in_block)
        non_attacking_counts.append(na_in_block)

    return attacking_counts, non_attacking_counts

def plot_cumulative_selections_over_blocks(data_folder, configs):
    """
    - 3×3 subplots
    - Columns = percentage of attacking builders
    - Rows = percentage of attacking users
    - Single text labels for "Percentage of Attacking Builders" (top),
      "Percentage of Attacking Users" (right), "Cumulative Selections" (left),
      and "Block Number" (bottom).
    """
    output_dir = 'figures/ss'
    os.makedirs(output_dir, exist_ok=True)

    # Gather unique builder/user counts from the configs
    builder_counts = sorted({c[0] for c in configs})
    user_counts = sorted({c[1] for c in configs})

    fig, axes = plt.subplots(
        nrows=len(user_counts),
        ncols=len(builder_counts),
        figsize=(9.5, 9),
        squeeze=False
    )

    # Font sizes
    label_font_size = 16
    tick_label_font_size = 16
    outer_label_font_size = 20

    y_limit = 1000
    handles, labels = [], []

    # Plot each subplot
    for b_attack, u_attack in configs:
        row_idx = user_counts.index(u_attack)
        col_idx = builder_counts.index(b_attack)
        ax = axes[row_idx, col_idx]

        filename = f"pbs_block_data_builders{b_attack}_users{u_attack}.csv"
        file_path = os.path.join(data_folder, filename)

        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            ax.text(0.5, 0.5, "File Not Found",
                    ha='center', va='center',
                    fontsize=label_font_size)
            ax.set_axis_off()
            continue

        att_counts, nonatt_counts = get_builder_counts_by_block(file_path, b_attack)
        x_vals = np.arange(len(att_counts))

        line1, = ax.plot(x_vals, np.cumsum(att_counts),
                         color='red', alpha=0.5, label=r"$\tau_{B_i} = \mathtt{attack}$")
        line2, = ax.plot(x_vals, np.cumsum(nonatt_counts),
                         color='blue', alpha=0.5, label=r"$\tau_{B_i} = \mathtt{benign}$")
        ax.set_ylim(0, y_limit)
        ax.set_yticks([0, 500, 1000])

        # Only gather legend handles once
        if not handles:
            handles.extend([line1, line2])
            labels.extend([r"$\tau_{B_i} = \mathtt{attack}$", r"$\tau_{B_i} = \mathtt{benign}$"])

        # Hide x-axis labels except bottom row
        if row_idx != len(user_counts) - 1:
            ax.tick_params(axis='x', labelbottom=False)
        # Hide y-axis labels except first column
        if col_idx != 0:
            ax.tick_params(axis='y', labelleft=False)

        ax.tick_params(axis='both', labelsize=tick_label_font_size)

    # Convert numeric builder counts to percentages and label columns
    for ax, bcount in zip(axes[0], builder_counts):
        pct_builders = (bcount / TOTAL_BUILDERS) * 100
        # Move pad down a bit from 15 to 10 if you want more space from the top label
        ax.set_title(f"{pct_builders:.0f}", fontsize=outer_label_font_size, pad=10)

    # Convert numeric user counts to percentages and label rows on the right
    for ax, ucount in zip(axes[:, -1], user_counts):
        pct_users = (ucount / TOTAL_USERS) * 100
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

    # Tight layout for subplots (ensures subplots themselves aren't overlapping)
    plt.tight_layout()

    # Adjust margins to make room for outer text, tweak as needed
    plt.subplots_adjust(left=0.12, right=0.88, top=0.83, bottom=0.12)

    # Single text labels
    # Top: "Percentage of Attacking Builders"
    fig.text(
        0.5, 0.91,  # Move down from 0.95 if needed
        r"MEV-Seeking Builders: $\tau_{B_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )
    # Right: "Percentage of Attacking Users"
    fig.text(
        0.95, 0.5,  # Move left from 0.92 if needed
        r"MEV-Seeking Users: $\tau_{U_i} = \mathtt{attack}$ (%)",
        ha='center', va='center',
        rotation=-90,
        fontsize=outer_label_font_size
    )
    # Left: "Cumulative Selections"
    fig.text(
        0.03, 0.5,
        "Cumulative Selections",
        ha='center', va='center',
        rotation='vertical',
        fontsize=outer_label_font_size
    )
    # Bottom: "Block Number"
    fig.text(
        0.5, 0.06,  # Move up from 0.06 if needed
        "Block Number",
        ha='center', va='center',
        fontsize=outer_label_font_size
    )

    # Legend in bottom-right
    fig.legend(handles, labels, loc='lower right',
               fontsize=label_font_size, frameon=False)

    out_path = os.path.join(output_dir, "pbs_cumulative_selection_3x3_grid.png")
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"3×3 grid plot saved to {out_path}")

if __name__ == "__main__":
    data_folder = "data/same_seed/pbs_visible80"
    # Example: (attacking_builders_count, attacking_users_count).
    configs = [
        (5, 0), (10, 0), (15, 0),
        (5, 25), (10, 25), (15, 25),
        (5, 50), (10, 50), (15, 50)
    ]
    plot_cumulative_selections_over_blocks(data_folder, configs)
